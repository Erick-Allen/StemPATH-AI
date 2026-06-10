from sentence_transformers import SentenceTransformer

from src.arango_client import get_app_db


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def main() -> None:
    db = get_app_db()
    documents = db.collection("documents")

    model = SentenceTransformer(MODEL_NAME)

    updated_count = 0

    for document in documents.all():
        content = document.get("content")

        if not content:
            continue

        embedding = model.encode(content).tolist()

        documents.update(
            {
                "_key": document["_key"],
                "embedding": embedding,
                "embedding_model": MODEL_NAME,
            }
        )

        updated_count += 1

    print(f"Generated embeddings for {updated_count} documents.")


if __name__ == "__main__":
    main()