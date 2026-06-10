import numpy as np
from sentence_transformers import SentenceTransformer

from src.arango_client import get_app_db


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class StemPathCore:
    def __init__(self):
        self.db = get_app_db()
        self.model = SentenceTransformer(MODEL_NAME)

    def ensure_ready(self) -> None:
        documents = self.db.collection("documents")
        sample = next(documents.all(), None)

        if not sample:
            raise RuntimeError("No RAG documents found. Run scripts.populate first.")

        if "embedding" not in sample:
            raise RuntimeError("No embeddings found. Run scripts.generate_embeddings first.")

    def cosine_similarity(self, a, b) -> float:
        a = np.array(a)
        b = np.array(b)

        denominator = np.linalg.norm(a) * np.linalg.norm(b)

        if denominator == 0:
            return 0.0

        return float(np.dot(a, b) / denominator)

    def search_documents(self, question: str, limit: int = 3) -> list[dict]:
        documents = self.db.collection("documents")
        question_embedding = self.model.encode(question).tolist()

        results = []

        for doc in documents.all():
            if "embedding" not in doc:
                continue

            results.append(
                {
                    "title": doc["title"],
                    "occupation_key": doc["occupation_key"],
                    "content": doc["content"],
                    "score": self.cosine_similarity(question_embedding, doc["embedding"]),
                }
            )

        return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]

    def get_graph_context(self, occupation_key: str) -> dict:
        occupation_id = f"occupations/{occupation_key}"

        query = """
        RETURN {
            domains: (
                FOR v IN OUTBOUND @occupation_id occupation_belongs_to_domain
                    RETURN v.name
            ),
            skills: (
                FOR v IN OUTBOUND @occupation_id occupation_requires_skill
                    RETURN v.name
            ),
            technologies: (
                FOR v IN OUTBOUND @occupation_id occupation_uses_technology
                    RETURN v.name
            ),
            tasks: (
                FOR v IN OUTBOUND @occupation_id occupation_performs_task
                    RETURN v.description
            ),
            knowledge: (
                FOR v IN OUTBOUND @occupation_id occupation_requires_knowledge
                    RETURN v.name
            )
        }
        """

        return list(
            self.db.aql.execute(
                query,
                bind_vars={"occupation_id": occupation_id},
            )
        )[0]

    def build_answer(self, question: str, top_result: dict, graph: dict) -> str:
        skills = ", ".join(graph.get("skills", [])[:6])
        technologies = ", ".join(graph.get("technologies", [])[:6])
        tasks = ", ".join(graph.get("tasks", [])[:3])
        domains = ", ".join(graph.get("domains", []))

        return f"""
        Best match: {top_result["title"]}

        This result was selected because its O*NET career document was the closest semantic match to the question: "{question}".

        Domain: {domains}

        Relevant skills: {skills}

        Relevant technologies: {technologies}

        Representative tasks: {tasks}
        """.strip()

    def query(self, question: str) -> tuple[str | None, list[dict]]:
        results = self.search_documents(question)

        if not results:
            return None, []

        top_result = results[0]
        graph = self.get_graph_context(top_result["occupation_key"])
        answer = self.build_answer(question, top_result, graph)

        for result in results:
            result["graph_context"] = self.get_graph_context(result["occupation_key"])

        return answer, results

    def list_career_options(self, limit: int = 200) -> list[dict]:
        query = """
        FOR occupation IN occupations
            SORT occupation.title
            LIMIT @limit
            RETURN {
                key: occupation._key,
                title: occupation.title
            }
        """

        return list(
            self.db.aql.execute(
                query,
                bind_vars={"limit": limit},
            )
        )

    def get_career_profile(self, occupation_key: str) -> dict | None:
        occupation = self.db.collection("occupations").get(occupation_key)

        if not occupation:
            return None

        return {
            "key": occupation["_key"],
            "title": occupation["title"],
            "description": occupation.get("description"),
            "graph_context": self.get_graph_context(occupation["_key"]),
        }

def retrieve_graphrag_context(question: str) -> dict:
    core = StemPathCore()
    core.ensure_ready()

    answer, results = core.query(question)

    return {
        "question": question,
        "answer": answer,
        "results": results,
    }

