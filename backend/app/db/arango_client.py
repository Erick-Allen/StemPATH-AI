import os

from arango import ArangoClient
from dotenv import load_dotenv

load_dotenv()


def get_arango_client() -> ArangoClient:
    return ArangoClient(
        hosts=os.getenv("ARANGO_URL", "http://localhost:8529")
    )


def get_system_db():
    client = get_arango_client()

    return client.db(
        "_system",
        username=os.getenv("ARANGO_USERNAME", "root"),
        password=os.getenv("ARANGO_PASSWORD", "rootpassword"),
    )


def get_app_db():
    client = get_arango_client()

    return client.db(
        os.getenv("ARANGO_DATABASE", "stem_career_graph"),
        username=os.getenv("ARANGO_USERNAME", "root"),
        password=os.getenv("ARANGO_PASSWORD", "rootpassword"),
    )