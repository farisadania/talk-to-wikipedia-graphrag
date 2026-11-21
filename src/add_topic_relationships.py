from src.graph_store import add_mentioned_topics, get_graph_driver


TOPIC_MAP = {
    "Artificial intelligence": [
        "Artificial intelligence",
        "Machine learning",
        "Natural language",
        "Neural network",
    ],
    "Machine learning": [
        "Artificial intelligence",
        "Machine learning",
        "Neural network",
        "Vector",
    ],
    "Large language model": [
        "Artificial intelligence",
        "Machine learning",
        "Natural language",
        "Retrieval",
    ],
    "Graph database": [
        "Graph",
        "Database",
        "Knowledge graph",
        "Retrieval",
    ],
    "Vector database": [
        "Vector",
        "Database",
        "Embeddings",
        "Retrieval",
    ],
    "Retrieval-augmented generation": [
        "Retrieval",
        "Large language model",
        "Embeddings",
        "Vector",
        "Knowledge graph",
    ],
}


def main() -> None:
    with get_graph_driver() as driver:
        for article_title, topics in TOPIC_MAP.items():
            add_mentioned_topics(driver, article_title, topics)
            print(f"Added topics for: {article_title}")


if __name__ == "__main__":
    main()