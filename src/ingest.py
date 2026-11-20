'''
Ingestion is run when you add or update the data.

It follows these steps:
1. Fetches Wikipedia articles for the selected topics.
2. Splits the article text into smaller chunks. Smaller pieces are easier to retrieve than whole articles.
3. Sends the chunks to the vector store. Chroma's embedding function turns each chunk into a numerical representation, or embedding, and stores it along with the text and metadata such as its title and source URL.
'''

import time
from urllib.parse import quote

import requests
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import load_config
from src.vector_store import add_documents


TOPICS = [
    "Artificial intelligence",
    "Machine learning",
    "Large language model",
    "Graph database",
    "Vector database",
    "Retrieval-augmented generation",
]


def fetch_article(title: str) -> Document:
    response = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "format": "json",
            "prop": "extracts", # requests the introductory/extracted article text rather than article metadata or revision details
            "explaintext": 1, # requests plain text instead of HTML
            "redirects": 1,
            "titles": title,
        },
        headers={"User-Agent": "TalkToDataGraphRAG/0.1 (learning project)"},
        timeout=30, # stops waiting after 30 seconds if Wikipedia doesn’t respond
    )
    response.raise_for_status()

    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError as error:
        raise RuntimeError(
            f"Wikipedia returned a non-JSON response for {title!r}. "
            f"Response began: {response.text[:200]!r}"
        ) from error

    pages = data["query"]["pages"].values()
    page = next(iter(pages))
    text = page.get("extract", "")

    if not text:
        raise RuntimeError(f"No article text returned for {title!r}")

    page_title = page["title"]
    url_title = quote(page_title.replace(" ", "_"))
    return Document(
        page_content=text,
        metadata={
            "title": page_title,
            "topic": title,
            "source": f"https://en.wikipedia.org/wiki/{url_title}",
        },
    )


def main() -> None:
    config = load_config()
    ingestion_config = config["ingestion"]

    documents = []
    for topic in TOPICS:
        print(f"Loading Wikipedia topic: {topic}")
        documents.append(fetch_article(topic))
        time.sleep(0.5)

    #  Split each article into small, overlapping chunks before embeddings are generated
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=ingestion_config["chunk_size"], # split at n characters
        chunk_overlap=ingestion_config["chunk_overlap"], # helps ensure that a sentence’s conclusion or a relevant passage isn’t lost because it happens to sit at the boundary
    )
    chunks = splitter.split_documents(documents)

    print(f"Loaded {len(documents)} articles; split them into {len(chunks)} chunks.")
    add_documents(chunks)


if __name__ == "__main__":
    main()