from neo4j import GraphDatabase

from src.config import load_config


def get_graph_driver():
    config = load_config()["graph_store"]

    return GraphDatabase.driver(
        config["uri"],
        auth=(config["username"], config["password"]),
    )


def verify_graph_connection() -> None:
    with get_graph_driver() as driver:
        driver.verify_connectivity()
        print("Connected to Neo4j.")