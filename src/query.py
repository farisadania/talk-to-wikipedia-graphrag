'''
User question
    ↓
nomic-embed-text converts the question into a vector
    ↓
Chroma compares it with stored document vectors
    ↓
Chroma returns the closest chunks
'''

from src.vector_store import get_vector_store


def main() -> None:
    vector_store = get_vector_store()

    question = input("Ask a question about the indexed Wikipedia articles: ").strip()
    if not question:
        print("Please enter a question.")
        return

    try:
        results = vector_store.similarity_search_with_score(question, k=4)
    except Exception as error:
        print(f"Search failed: {error}")
        return

    if not results:
        print("No matching chunks found. Run the ingestion script first.")
        return

    for index, (document, score) in enumerate(results, start=1):
        title = document.metadata.get("title", "Unknown article")
        source = document.metadata.get("source", "Source URL unavailable")

        print(f"\n--- Result {index} | distance: {score:.4f} ---")
        print(f"Article: {title}")
        print(f"Source: {source}")
        print(document.page_content[:1000])


if __name__ == "__main__":
    main()