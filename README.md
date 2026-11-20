# Talk to Wikipedia: Conversational Knowledge Explorer
Build a natural language interface ("Chat with Wikipedia") that allows users to ask questions about Wikipedia articles, retrieves the most relevant passages (using a vector database and GraphRAG for traversing relationships among articles/concepts), and provides insightful, context-rich answers.

# Key Components
LLM: Ollama with qwen2.5:7b or llama3.1:8b
Embeddings: nomic-embed-text or bge-m3
Vector database: ChromaDB
Graph database: Neo4j Community Edition locally
Orchestration: LangChain or LlamaIndex
UI: Streamlit
Dataset: Wikipedia/Wikidata subset

# Why This Project?
- Combines search, semantic retrieval, and graph-based grounding—the frontier of enterprise “Talk to Data.”
- Use of public data means it’s easily reproducible.
- Shows both RAG and advanced GraphRAG patterns.
- Demonstrates both practical (search, summarization) and advanced reasoning (graph-based navigation).
