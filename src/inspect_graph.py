from src.graph_store import get_graph_driver


def print_query_results(title: str, query: str) -> None:
    print(f"\n{title}")
    print("-" * len(title))

    with get_graph_driver() as driver:
        records, _, _ = driver.execute_query(query)

    if not records:
        print("No results found.")
        return

    for record in records:
        print(record.data())


def main() -> None:
    print_query_results(
        "Node counts",
        """
        MATCH (node)
        UNWIND labels(node) AS label
        RETURN label, count(*) AS count
        ORDER BY label
        """,
    )

    print_query_results(
        "Relationship counts",
        """
        MATCH ()-[relationship]->()
        RETURN type(relationship) AS relationship,
               count(*) AS count
        ORDER BY relationship
        """,
    )

    print_query_results(
        "Article-to-topic examples",
        """
        MATCH (article:Article)-[:HAS_TOPIC]->(topic:Topic)
        RETURN article.title AS article,
               topic.name AS topic
        ORDER BY article
        LIMIT 10
        """,
    )

    print_query_results(
        "Article-to-chunk examples",
        """
        MATCH (article:Article)-[:HAS_CHUNK]->(chunk:Chunk)
        RETURN article.title AS article,
               substring(chunk.text, 0, 160) AS chunk_preview
        ORDER BY article
        LIMIT 5
        """,
    )


if __name__ == "__main__":
    main()