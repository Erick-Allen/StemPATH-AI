import numpy as np
import os
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from src.arango_client import get_app_db


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

load_dotenv()

class StemPathCore:
    def __init__(self):
        self.db = get_app_db()
        self.model = SentenceTransformer(MODEL_NAME)
        self.use_llm = os.getenv("USE_LLM", "false").lower() == "true"
        self.llm_model = os.getenv("LLM_MODEL", "local-model")

        self.llm = None

        if self.use_llm:
            self.llm = OpenAI(
                base_url=os.getenv("LLM_URL", "http://localhost:11434/v1"),
                api_key=os.getenv("LLM_API_KEY", "not-needed"),
            )

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

        return (
            f"Best match: {top_result['title']}\n\n"
            f"This result was selected because its O*NET career document was the closest semantic match "
            f'to the question: "{question}".\n\n'
            f"Domain: {domains}\n\n"
            f"Relevant skills: {skills}\n\n"
            f"Relevant technologies: {technologies}\n\n"
            f"Representative tasks: {tasks}"
        )

    def query(self, question: str) -> tuple[str | None, list[dict]]:
        results = self.search_documents(question)

        if not results:
            return None, []

        for result in results:
            result["graph_context"] = self.get_graph_context(result["occupation_key"])

        top_result = results[0]
        graph = top_result["graph_context"]

        answer = self.generate_llm_answer(question, top_result, graph)

        if not answer:
            answer = self.build_answer(question, top_result, graph)

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
    
    def generate_llm_answer(self, question: str, top_result: dict, graph: dict) -> str | None:
        if not self.use_llm or not self.llm:
            return None

        skills = ", ".join(graph.get("skills", [])[:8])
        technologies = ", ".join(graph.get("technologies", [])[:8])
        tasks = "\n".join(f"- {task}" for task in graph.get("tasks", [])[:5])
        knowledge = ", ".join(graph.get("knowledge", [])[:8])
        domains = ", ".join(graph.get("domains", []))

        prompt = f"""
        User question:
        {question}

        Matched occupation:
        {top_result["title"]}

        Career domain:
        {domains}

        O*NET career document:
        {top_result["content"]}

        Related skills:
        {skills}

        Related technologies:
        {technologies}

        Representative tasks:
        {tasks}

        Knowledge areas:
        {knowledge}

        Write a concise STEM career research answer using only the provided context.
        Do not invent salary, job openings, degree requirements, or facts not shown here.
        """.strip()

        try:
            response = self.llm.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a grounded STEM career research assistant using O*NET graph context.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.2,
                max_tokens=500,
            )

            return response.choices[0].message.content.strip()

        except Exception as error:
            print(f"LLM generation failed: {error}")
            return None

def retrieve_graphrag_context(question: str) -> dict:
    core = StemPathCore()
    core.ensure_ready()

    answer, results = core.query(question)

    return {
        "question": question,
        "answer": answer,
        "results": results,
    }

