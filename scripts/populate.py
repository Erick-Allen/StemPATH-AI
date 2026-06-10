from scripts.setup_db import main as setup_db
from scripts.load_onet_data import main as load_onet_data
from scripts.generate_embeddings import main as generate_embeddings


def main() -> None:
    print("Setting up ArangoDB database and graph...")
    setup_db()

    print("Loading O*NET STEM career data...")
    load_onet_data()

    print("Generating document embeddings...")
    generate_embeddings()

    print("Population pipeline complete.")


if __name__ == "__main__":
    main()