import json
from pathlib import Path

from app.db.arango_client import get_app_db


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "seed_careers.json"


def normalize_key(value: str) -> str:
    return (
        value.lower()
        .replace("/", " ")
        .replace("-", " ")
        .replace("&", "and")
        .replace(" ", "_")
    )


def upsert_document(collection, key: str, data: dict) -> None:
    if collection.has(key):
        collection.update({"_key": key, **data})
    else:
        collection.insert({"_key": key, **data})


def upsert_edge(collection, key: str, from_id: str, to_id: str) -> None:
    if not collection.has(key):
        collection.insert({
            "_key": key,
            "_from": from_id,
            "_to": to_id,
        })


def build_career_text(career: dict) -> str:
    return f"""
{career["title"]}

Description:
{career["description"]}

Career domain:
{career["domain"]}

Important skills:
{", ".join(career["skills"])}

Common technologies:
{", ".join(career["technologies"])}

Common tasks:
{", ".join(career["tasks"])}
""".strip()


def main() -> None:
    db = get_app_db()

    documents = db.collection("documents")
    document_edges = db.collection("document_describes_occupation")

    with DATA_PATH.open("r", encoding="utf-8") as file:
        careers = json.load(file)

    for career in careers:
        occupation_key = career["key"]
        document_key = f"seed_{occupation_key}"
        occupation_id = f"occupations/{occupation_key}"
        document_id = f"documents/{document_key}"

        upsert_document(
            documents,
            document_key,
            {
                "title": career["title"],
                "source": "seed_careers.json",
                "source_type": "seed_data",
                "occupation_key": occupation_key,
                "content": build_career_text(career),
            },
        )

        edge_key = normalize_key(f"{document_key}_describes_{occupation_key}")
        upsert_edge(
            document_edges,
            edge_key,
            document_id,
            occupation_id,
        )

    print(f"Built {len(careers)} RAG documents.")


if __name__ == "__main__":
    main()