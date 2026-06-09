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


def upsert_edge(collection, from_id: str, to_id: str) -> None:
    edge_key = normalize_key(f"{from_id}_{to_id}".replace("/", "_"))

    if not collection.has(edge_key):
        collection.insert({
            "_key": edge_key,
            "_from": from_id,
            "_to": to_id,
        })


def main() -> None:
    db = get_app_db()

    occupations = db.collection("occupations")
    skills = db.collection("skills")
    technologies = db.collection("technologies")
    tasks = db.collection("tasks")
    career_domains = db.collection("career_domains")

    requires_skill = db.collection("occupation_requires_skill")
    uses_technology = db.collection("occupation_uses_technology")
    performs_task = db.collection("occupation_performs_task")
    belongs_to_domain = db.collection("occupation_belongs_to_domain")

    with DATA_PATH.open("r", encoding="utf-8") as file:
        careers = json.load(file)

    for career in careers:
        occupation_key = career["key"]
        occupation_id = f"occupations/{occupation_key}"

        upsert_document(
            occupations,
            occupation_key,
            {
                "title": career["title"],
                "description": career["description"],
            },
        )

        domain_key = normalize_key(career["domain"])
        domain_id = f"career_domains/{domain_key}"

        upsert_document(
            career_domains,
            domain_key,
            {"name": career["domain"]},
        )
        upsert_edge(belongs_to_domain, occupation_id, domain_id)

        for skill in career["skills"]:
            skill_key = normalize_key(skill)
            skill_id = f"skills/{skill_key}"

            upsert_document(skills, skill_key, {"name": skill})
            upsert_edge(requires_skill, occupation_id, skill_id)

        for technology in career["technologies"]:
            technology_key = normalize_key(technology)
            technology_id = f"technologies/{technology_key}"

            upsert_document(technologies, technology_key, {"name": technology})
            upsert_edge(uses_technology, occupation_id, technology_id)

        for task in career["tasks"]:
            task_key = normalize_key(task)
            task_id = f"tasks/{task_key}"

            upsert_document(tasks, task_key, {"description": task})
            upsert_edge(performs_task, occupation_id, task_id)

    print(f"Seeded {len(careers)} STEM careers into ArangoDB.")


if __name__ == "__main__":
    main()