import numpy as np
from sentence_transformers import SentenceTransformer

from src.arango_client import get_app_db


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)


def cosine_similarity(a, b) -> float:
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def search_documents(question: str, limit: int = 3) -> list[dict]:
    db = get_app_db()
    documents = db.collection("documents")
    question_embedding = model.encode(question).tolist()

    results = []

    for doc in documents.all():
        if "embedding" not in doc:
            continue

        results.append({
            "title": doc["title"],
            "occupation_key": doc["occupation_key"],
            "content": doc["content"],
            "score": cosine_similarity(question_embedding, doc["embedding"]),
        })

    return sorted(results, key=lambda x: x["score"], reverse=True)[:limit]


def get_graph_context(occupation_key: str) -> dict:
    db = get_app_db()
    occupation_id = f"occupations/{occupation_key}"

    query = """
    RETURN {
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
        ),
        domains: (
            FOR v IN OUTBOUND @occupation_id occupation_belongs_to_domain
                RETURN v.name
        )
    }
    """

    return list(db.aql.execute(query, bind_vars={"occupation_id": occupation_id}))[0]


def retrieve_graphrag_context(question: str) -> dict:
    top_doc = search_documents(question, limit=1)[0]
    graph = get_graph_context(top_doc["occupation_key"])

    return {
        "question": question,
        "matched_occupation": top_doc["title"],
        "similarity_score": round(top_doc["score"], 4),
        "rag_document": top_doc["content"],
        "graph_context": graph,
    }