from neo4j import GraphDatabase

from src.config import load_config


def get_graph_driver():
    # Load graph storage config
    config = load_config()["graph_store"]

    return GraphDatabase.driver(
        config["uri"],
        auth=(config["username"], config["password"]),
    )


def verify_graph_connection() -> None:
    with get_graph_driver() as driver:
        driver.verify_connectivity()
        print("Connected to Neo4j.")


def find_article_context(driver, title: str) -> list[dict]:
    records, _, _ = driver.execute_query(
    """
    MATCH (article:Article {title: $title})
    OPTIONAL MATCH (article)-[:HAS_TOPIC]->(topic:Topic)
    OPTIONAL MATCH (article)-[:HAS_CHUNK]->(chunk:Chunk)
    RETURN article.title AS article,
           article.source AS source,
           collect(DISTINCT topic.name) AS topics,
           collect(DISTINCT chunk.text) AS chunks
    """,
    title=title,
    database_="neo4j",
    )

    return [record.data() for record in records]


def find_related_articles(driver, title: str, limit: int = 10) -> list[dict]:
    records, _, _ = driver.execute_query(
        """
        MATCH (article:Article {title: $title})
        -[:HAS_TOPIC|MENTIONS_TOPIC]->(topic:Topic)
        <-[:HAS_TOPIC|MENTIONS_TOPIC]-(related:Article)
        WHERE related.title <> article.title
        WITH related,
             collect(DISTINCT topic.name) AS shared_topics,
             count(DISTINCT topic) AS topic_count
        RETURN related.title AS title,
               related.source AS source,
               shared_topics,
               topic_count
        ORDER BY topic_count DESC, title ASC
        LIMIT $limit
        """,
        title=title,
        limit=limit,
        database_="neo4j",
    )

    return [record.data() for record in records]


def add_mentioned_topics(
    driver,
    title: str,
    topics: list[str],
) -> None:
    driver.execute_query(
        """
        MATCH (article:Article {title: $title})
        UNWIND $topics AS topic_name
        MERGE (topic:Topic {name: topic_name})
        MERGE (article)-[:MENTIONS_TOPIC]->(topic)
        """,
        title=title,
        topics=topics,
        database_="neo4j",
    )