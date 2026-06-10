import os

from dotenv import load_dotenv

from src.arango_client import get_system_db, get_app_db

load_dotenv()

DATABASE_NAME = os.getenv("ARANGO_DATABASE", "stem_career_graph")
GRAPH_NAME = os.getenv("ARANGO_GRAPH", "stem_career_graph")

VERTEX_COLLECTIONS = [
    "occupations",
    "skills",
    "technologies",
    "tasks",
    "knowledge_areas",
    "career_domains",
    "documents",
]

EDGE_COLLECTIONS = [
    "occupation_requires_skill",
    "occupation_uses_technology",
    "occupation_performs_task",
    "occupation_requires_knowledge",
    "occupation_belongs_to_domain",
    "document_describes_occupation",
]


def ensure_database() -> None:
    system_db = get_system_db()

    if not system_db.has_database(DATABASE_NAME):
        system_db.create_database(DATABASE_NAME)
        print(f"Created database: {DATABASE_NAME}")
    else:
        print(f"Database already exists: {DATABASE_NAME}")


def ensure_collections() -> None:
    db = get_app_db()

    for collection_name in VERTEX_COLLECTIONS:
        if not db.has_collection(collection_name):
            db.create_collection(collection_name)
            print(f"Created vertex collection: {collection_name}")
        else:
            print(f"Vertex collection already exists: {collection_name}")

    for collection_name in EDGE_COLLECTIONS:
        if not db.has_collection(collection_name):
            db.create_collection(collection_name, edge=True)
            print(f"Created edge collection: {collection_name}")
        else:
            print(f"Edge collection already exists: {collection_name}")


def ensure_graph() -> None:
    db = get_app_db()

    if db.has_graph(GRAPH_NAME):
        print(f"Graph already exists: {GRAPH_NAME}")
        return

    graph = db.create_graph(GRAPH_NAME)

    graph.create_edge_definition(
        edge_collection="occupation_requires_skill",
        from_vertex_collections=["occupations"],
        to_vertex_collections=["skills"],
    )

    graph.create_edge_definition(
        edge_collection="occupation_uses_technology",
        from_vertex_collections=["occupations"],
        to_vertex_collections=["technologies"],
    )

    graph.create_edge_definition(
        edge_collection="occupation_performs_task",
        from_vertex_collections=["occupations"],
        to_vertex_collections=["tasks"],
    )

    graph.create_edge_definition(
        edge_collection="occupation_requires_knowledge",
        from_vertex_collections=["occupations"],
        to_vertex_collections=["knowledge_areas"],
    )

    graph.create_edge_definition(
        edge_collection="occupation_belongs_to_domain",
        from_vertex_collections=["occupations"],
        to_vertex_collections=["career_domains"],
    )

    graph.create_edge_definition(
        edge_collection="document_describes_occupation",
        from_vertex_collections=["documents"],
        to_vertex_collections=["occupations"],
    )

    print(f"Created graph: {GRAPH_NAME}")


def main() -> None:
    ensure_database()
    ensure_collections()
    ensure_graph()
    print("ArangoDB setup complete.")


if __name__ == "__main__":
    main()