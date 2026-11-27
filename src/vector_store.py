'''
This vectore storage file consists of methods called inside the ingestion process to
1. convert text chunks into vectors for semantic search
2. store the vector chunks in Chroma
'''
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from src.config import ROOT_DIR, load_config


def get_vector_store() -> Chroma:
    # Load vector storage config
    config = load_config()

    # Set path to store Chroma outputs
    persist_path = Path(config["vector_store"]["persist_directory"])
    if not persist_path.is_absolute():
        persist_path = ROOT_DIR / persist_path
    persist_path.mkdir(parents=True, exist_ok=True)

    # Turns chunks text into vectors for semantic search
    embeddings = OllamaEmbeddings(
        model=config["ollama"]["embed_model"],
        base_url=config["ollama"]["base_url"],
    )

    # Store vectors in Chroma (an open-source vector and search database)
    return Chroma(
        collection_name="wikipedia_articles",
        persist_directory=str(persist_path),
        embedding_function=embeddings,
    )


def add_documents(documents: list[Document]) -> None:
    if not documents:
        print("No document chunks to add.")
        return

    get_vector_store().add_documents(documents)
    print(f"Added {len(documents)} chunks to Chroma.")