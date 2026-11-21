from src.graph_store import find_related_articles, get_graph_driver


def main() -> None:
    with get_graph_driver() as driver:
        articles = find_related_articles(
            driver,
            "Artificial intelligence",
        )

    if not articles:
        print("No related articles found.")
        return

    for article in articles:
        print(article)


if __name__ == "__main__":
    main()