from scripts.setup_db import main as setup_db
from scripts.load_seed_careers import main as load_seed_careers
from scripts.build_rag_documents import main as build_rag_documents


def main() -> None:
    print("Setting up ArangoDB database and graph...")
    setup_db()

    print("Loading seed STEM career graph data...")
    load_seed_careers()

    print("Building RAG documents from career data...")
    build_rag_documents()

    print("Population pipeline complete.")


if __name__ == "__main__":
    main()