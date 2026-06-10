import re
import hashlib
from pathlib import Path

import pandas as pd

from src.arango_client import get_app_db


# [Config] Source files and limits
RAW = Path("data")
MAX_OCCUPATIONS = 100

FILES = {
    "occupations": RAW / "Occupation Data.txt",
    "skills": RAW / "Essential Skills.txt",
    "software": RAW / "Software Skills.txt",
    "tasks": RAW / "Task Statements.txt",
    "knowledge": RAW / "Knowledge.txt",
}

STEM_KEYWORDS = [
    "software", "developer", "programmer", "data", "database", "computer",
    "cyber", "security", "engineer", "mathematician", "statistician",
    "biologist", "chemist", "physicist", "scientist", "environmental",
]


# [Helpers] Clean keys and avoid duplicate edges
def key(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value.lower()).strip("_")
    return value[:80]


def edge_key(a: str, b: str) -> str:
    return hashlib.sha1(f"{a}->{b}".encode()).hexdigest()


def upsert(collection, doc_key: str, data: dict):
    doc = {"_key": doc_key, **data}
    collection.update(doc) if collection.has(doc_key) else collection.insert(doc)


def link(collection, from_id: str, to_id: str):
    k = edge_key(from_id, to_id)

    if not collection.has(k):
        collection.insert({"_key": k, "_from": from_id, "_to": to_id})


# [Data loading] Read O*NET text files and group rows by occupation code
def read(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep="\t", dtype=str, encoding="utf-8-sig").fillna("")
    df.columns = df.columns.str.strip()
    return df


def group(df: pd.DataFrame, column: str) -> dict[str, list[str]]:
    return (
        df.groupby("O*NET-SOC Code")[column]
        .apply(lambda x: list(dict.fromkeys(x.tolist()))[:10])
        .to_dict()
    )


# [Filtering] Keep STEM-related occupations only
def is_stem(row) -> bool:
    code = row["O*NET-SOC Code"]
    title = row["Title"].lower()

    return (
        code.startswith("15-")
        or code.startswith("17-")
        or any(word in title for word in STEM_KEYWORDS)
    )


def domain_for(code: str, title: str) -> str:
    title = title.lower()

    if "software" in title or "developer" in title or "programmer" in title:
        return "Software Engineering"
    if "data" in title:
        return "Data Science"
    if "cyber" in title or "security" in title:
        return "Cybersecurity"
    if "database" in title:
        return "Database Systems"
    if code.startswith("17-") or "engineer" in title:
        return "Engineering"
    if code.startswith("15-"):
        return "Technology"

    return "Science"


def main():
    db = get_app_db()

    # [Collections] Vertex collections
    occupations = db.collection("occupations")
    skills = db.collection("skills")
    technologies = db.collection("technologies")
    tasks = db.collection("tasks")
    knowledge = db.collection("knowledge_areas")
    domains = db.collection("career_domains")
    documents = db.collection("documents")

    # [Collections] Edge collections
    skill_edges = db.collection("occupation_requires_skill")
    tech_edges = db.collection("occupation_uses_technology")
    task_edges = db.collection("occupation_performs_task")
    knowledge_edges = db.collection("occupation_requires_knowledge")
    domain_edges = db.collection("occupation_belongs_to_domain")
    document_edges = db.collection("document_describes_occupation")

    # [Load] Read and organize O*NET data
    occ_df = read(FILES["occupations"])
    skill_map = group(read(FILES["skills"]), "Element Name")
    tech_map = group(read(FILES["software"]), "Workplace Example")
    task_map = group(read(FILES["tasks"]), "Task")
    knowledge_map = group(read(FILES["knowledge"]), "Element Name")

    stem_occupations = occ_df[occ_df.apply(is_stem, axis=1)].head(MAX_OCCUPATIONS)

    # [Ingest] Create graph nodes, edges, and RAG documents
    for _, row in stem_occupations.iterrows():
        code = row["O*NET-SOC Code"]
        title = row["Title"]
        description = row["Description"]

        occ_key = key(code)
        occ_id = f"occupations/{occ_key}"

        domain = domain_for(code, title)
        domain_key = key(domain)
        domain_id = f"career_domains/{domain_key}"

        occ_skills = skill_map.get(code, [])
        occ_tech = tech_map.get(code, [])
        occ_tasks = task_map.get(code, [])
        occ_knowledge = knowledge_map.get(code, [])

        upsert(occupations, occ_key, {
            "onet_code": code,
            "title": title,
            "description": description,
            "source": "O*NET",
        })

        upsert(domains, domain_key, {"name": domain})
        link(domain_edges, occ_id, domain_id)

        for item in occ_skills:
            item_key = key(item)
            upsert(skills, item_key, {"name": item})
            link(skill_edges, occ_id, f"skills/{item_key}")

        for item in occ_tech:
            item_key = key(item)
            upsert(technologies, item_key, {"name": item})
            link(tech_edges, occ_id, f"technologies/{item_key}")

        for item in occ_tasks:
            item_key = key(item)
            upsert(tasks, item_key, {"description": item})
            link(task_edges, occ_id, f"tasks/{item_key}")

        for item in occ_knowledge:
            item_key = key(item)
            upsert(knowledge, item_key, {"name": item})
            link(knowledge_edges, occ_id, f"knowledge_areas/{item_key}")

        # [RAG document] One searchable document per occupation
        content = f"""
{title}

Domain: {domain}

Description:
{description}

Skills:
{", ".join(occ_skills)}

Technologies:
{", ".join(occ_tech)}

Tasks:
{", ".join(occ_tasks)}

Knowledge:
{", ".join(occ_knowledge)}
""".strip()

        doc_key = f"onet_{occ_key}"

        upsert(documents, doc_key, {
            "title": title,
            "source": "O*NET",
            "source_type": "occupation_profile",
            "occupation_key": occ_key,
            "content": content,
        })

        link(document_edges, f"documents/{doc_key}", occ_id)

    print(f"Loaded {len(stem_occupations)} STEM occupations from O*NET.")


if __name__ == "__main__":
    main()