from src.graph_store import find_article_context, get_graph_driver


def main() -> None:
    with get_graph_driver() as driver:
        results = find_article_context(
            driver,
            "Artificial intelligence",
        )

    for result in results:
        print("Article:", result["article"])
        print("Topics:", result["topics"])
        print("Chunk count:", len(result["chunks"]))
        print("First chunk:", result["chunks"][0][:500])


if __name__ == "__main__":
    main()