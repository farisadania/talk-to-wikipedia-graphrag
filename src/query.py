'''
User question
    ↓
nomic-embed-text converts the question into a vector
    ↓
Chroma compares it with stored document vectors
    ↓
Chroma returns the closest chunks
'''

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from src.config import load_config
from src.graph_store import (
    find_article_context,
    find_related_articles,
    get_graph_driver,
)
from src.vector_store import get_vector_store


def main() -> None:
    question = input(
        "Ask a question about the indexed Wikipedia articles: "
    ).strip()

    if not question:
        print("Please enter a question.")
        return

    # Load settings and search Chroma for the most relevant chunks.
    config = load_config()
    vector_store = get_vector_store()

    try:
        direct_results = vector_store.similarity_search_with_score(
            question,
            k=4,
        )
    except Exception as error:
        print(f"Chroma search failed: {error}")
        return

    if not direct_results:
        print("No matching chunks found. Run the ingestion script first.")
        return

    article_titles = []
    evidence_sections = []

    print("\nDirect Chroma matches")
    print("----------------------")

    for index, (document, score) in enumerate(direct_results, start=1):
        title = document.metadata.get("title", "Unknown article")
        source = document.metadata.get("source", "Source unavailable")

        if title != "Unknown article":
            article_titles.append(title)

        print(f"\nResult {index}")
        print(f"Article: {title}")
        print(f"Source: {source}")
        print(f"Distance: {score:.4f}")
        print(document.page_content[:500])

        evidence_sections.append(
            f"""
            [Direct evidence {index}]
            Article: {title}
            Source: {source}
            Text:
            {document.page_content}
            """.strip()
                    )

    unique_titles = list(dict.fromkeys(article_titles))

    print("\nNeo4j graph expansion")
    print("---------------------")

    try:
        with get_graph_driver() as driver:
            seen_related_titles = set()

            for title in unique_titles:
                article_context = find_article_context(driver, title)
                related_articles = find_related_articles(driver, title)

                print(f"\nGraph context for: {title}")

                for article in article_context:
                    topics = article.get("topics", [])
                    chunks = article.get("chunks", [])

                    print(f"Topics: {topics}")
                    print(f"Chunks: {len(chunks)}")

                    # Add a few chunks from the matched article as graph evidence.
                    for chunk in chunks[:2]:
                        evidence_sections.append(
                            f"""
                            [Graph evidence]
                            Article: {article.get("article", title)}
                            Related through: article traversal
                            Text:
                            {chunk[:1500]}
                            """.strip()
                                                    )

                print("Related articles:")

                if not related_articles:
                    print("- None found")

                for related in related_articles:
                    related_title = related.get("title", "Unknown article")
                    shared_topics = related.get("shared_topics", [])

                    print(f"- {related_title}")
                    if shared_topics:
                        print(f"  Shared topics: {shared_topics}")

                    # Avoid adding the same related article more than once.
                    if (
                        related_title == "Unknown article"
                        or related_title in seen_related_titles
                    ):
                        continue

                    seen_related_titles.add(related_title)

                    # Follow the graph relationship to retrieve chunks from
                    # the related article, not just its title.
                    related_context = find_article_context(driver, related_title)

                    for related_article in related_context:
                        for chunk in related_article.get("chunks", [])[:2]:
                            evidence_sections.append(
                                f"""
                    [Graph-expanded evidence]
                    Article: {related_title}
                    Source: {related_article.get("source", "Unavailable")}
                    Shared topics: {shared_topics}
                    Text:
                    {chunk[:1500]}
                    """.strip()
                            )

    except Exception as error:
        print(f"\nNeo4j graph retrieval failed: {error}")
        print("Continuing with the direct Chroma matches only.")

    # Use the configured Ollama chat model; "llama3.2" is the fallback.
    ollama_config = config.get("ollama", {})
    chat_model = ollama_config.get("chat_model", "llama3.2")
    base_url = ollama_config.get("base_url", "http://localhost:11434")

    context = "\n\n".join(evidence_sections)

    messages = [
        SystemMessage(
            content=(
                "Answer the user's question using only the supplied evidence. "
                "Do not make up facts. Cite the article title and URL when a "
                "URL is available in the evidence. If the evidence does not "
                "answer the question, say what information is missing."
            )
        ),
        HumanMessage(
            content=f"""
                    Question:
                    {question}

                    Retrieved evidence:
                    {context}
                    """.strip()
                            ),
                        ]

    print("\nGraphRAG answer")
    print("---------------")

    try:
        chat = ChatOllama(
            model=chat_model,
            base_url=base_url,
            temperature=0,
        )
        response = chat.invoke(messages)
        print(response.content)
    except Exception as error:
        print(f"Could not generate an answer with Ollama: {error}")
        print(
            f"Check that Ollama is running and that the model "
            f"{chat_model!r} is available."
        )


if __name__ == "__main__":
    main()