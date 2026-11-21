# Talk to Wikipedia GraphRAG — Project Notes

**Steps and project explanation**  
**Date shown in the example:** Friday, November 20, 2026

## 1. Project Objective

Talk to Wikipedia GraphRAG is a local question-answering project. It retrieves information from a small collection of Wikipedia articles and uses that evidence to answer a user's question.

The project combines three main capabilities:

- **Vector retrieval:** Finds text passages whose meaning is similar to a question.
- **Graph retrieval:** Follows explicit relationships among articles, topics, and text chunks.
- **Answer generation:** Sends the retrieved evidence to a locally running language model.

```text
Question
   ↓
Ollama embedding model represents the question as a vector
   ↓
Chroma finds semantically similar text chunks
   ↓
Python gets the matching article titles
   ↓
Neo4j follows article, topic, and chunk relationships
   ↓
Python combines the evidence
   ↓
Ollama chat model generates an answer from the evidence
```

## 2. What Each Technology Does

### Python

Python runs the project: downloading article text, splitting it into chunks, creating vector and graph records, asking retrieval queries, and calling Ollama to generate an answer.

### Ollama

Ollama runs AI models locally. The embedding model turns text and questions into numerical vectors. The chat model writes an answer using the evidence provided by the Python program.

- `nomic-embed-text` — embedding model used for vector search.
- `llama3.1:8b` — chat model used in the example configuration. A smaller model can be selected if answer generation is too slow.
- Default local Ollama address: `http://localhost:11434`.

### Chroma

Chroma is the vector database. It stores each chunk's embedding together with its text and metadata, such as the article title and source URL. When a user asks a question, Chroma compares the question embedding with stored chunk embeddings and returns the closest matches.

**Chroma answers:** “Which stored passages are semantically similar to this question?”

Chroma is persisted locally under the configured directory, for example `data/chroma`.

### Neo4j

Neo4j is the graph database. It stores entities as nodes and their connections as relationships. Python connects to Neo4j using the Neo4j Python driver and sends Cypher queries from the project code. Neo4j Browser is optional; the application's graph queries can all be run from Python.

**Neo4j answers:** “What is connected to this article, and how?”

### LangChain and the Neo4j Python Driver

- LangChain provides Python interfaces for documents, text splitting, Chroma, Ollama embeddings, and Ollama chat models.
- The `neo4j` Python package connects to Neo4j and executes Cypher queries.
- Cypher is the query language sent to Neo4j. The query is written in Python as a string, and the Python driver executes it.

## 3. The Graph and Its Relationships

The initial graph model contains three node labels:

- **Article** — a Wikipedia article.
- **Topic** — a topic associated with an article.
- **Chunk** — a piece of article text used for retrieval.

The initial relationships are directed:

```text
(Article)-[:HAS_TOPIC]->(Topic)
(Article)-[:HAS_CHUNK]->(Chunk)
```

The arrow is important: an Article points to its Topic and to its Chunk. A relationship is not automatically bidirectional, although a Cypher query can match the path in either direction when written to do so.

Later, `MENTIONS_TOPIC` relationships were added to connect articles through shared concepts:

```text
(Article)-[:MENTIONS_TOPIC]->(Topic)
```

For example, two articles sharing the same topic node can be traversed as:

```text
(Article A)-[:MENTIONS_TOPIC]->(Topic)<-[:MENTIONS_TOPIC]-(Article B)
```

This path allows Neo4j to find related articles. The relationship means the articles are connected through a shared topic; it does not, by itself, prove that their text makes the same claim.

## 4. Chronological Setup and Coding Steps

### Step 1 — Create the Project Virtual Environment

A virtual environment was created in the project directory so project packages are isolated from other Python installations.

```powershell
cd C:\Users\user\Documents\GitHub\talk-to-wikipedia-graphrag
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

The prompt displaying `(.venv)` indicates that the environment is active.

Run project commands from the repository root, for example:

```powershell
.\.venv\Scripts\python.exe -m src.query
```

### Step 2 — Install and Check Ollama

Ollama was installed on Windows so embedding and chat models can run locally. Its command-line program was used to check the installation and download models.

```powershell
ollama --version
ollama pull llama3.1:8b
ollama pull nomic-embed-text
ollama run llama3.1:8b "Reply briefly: setup successful"
```

Ollama needs to be running when the Python project requests embeddings or generates an answer. The embedding model configured in the project should remain the same for indexing and querying.

### Step 3 — Install Python Packages

Packages were installed in the virtual environment. The project's `requirements.txt` includes the core dependencies:

```text
pyyaml
requests
langchain-core
langchain-text-splitters
langchain-chroma
langchain-ollama
neo4j
```

Install them with:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Chroma's LangChain integration is provided by `langchain-chroma`; the underlying Chroma package is installed as a dependency. If a package is missing, install it into this same environment with:

```powershell
.\.venv\Scripts\python.exe -m pip install PACKAGE_NAME
```

### Step 4 — Install Neo4j Desktop and Create a Local Database

Neo4j Desktop manages local Neo4j installations and databases. It is a management application; the Neo4j database instance is the database process that Python connects to. The database must be running before the Python application can query it.

1. Download and install **Neo4j Desktop** for Windows from Neo4j's official download page.
2. Open Neo4j Desktop and sign in or complete the setup steps it presents.
3. Create a project, or open an existing project.
4. Choose **Add** or **Create a DBMS**. The exact button wording can vary by Desktop version.
5. Choose a Neo4j version offered by Desktop, enter a database name, and set a password for the `neo4j` user. Save the password securely; the Python code needs the same password.
6. Create the database. Desktop may download the selected Neo4j version before creation is complete.
7. Click **Start** for the database instance. Wait until Desktop shows that it is running.
8. Use the instance's connection details. A typical local Bolt address is `bolt://localhost:7687`; confirm the actual address in Desktop if yours differs.
9. The default database name is commonly `neo4j`. Use the database name shown by Desktop in the Python configuration.

**DBMS versus database:** In Desktop, a DBMS is the running Neo4j server instance. It can contain one or more databases. For this project, the Python driver connects to the running instance and queries the configured database, usually named `neo4j`.

**Neo4j Browser:** Desktop may provide a Browser button for optional manual inspection and visualization. It is not required for the Python workflow in this project. The Python scripts execute the graph queries themselves.

### Step 5 — Configure the Project

The root-level `config.yaml` stores model, storage, and connection settings. The Neo4j password must be the one set when creating the local database in Desktop.

```yaml
ollama:
  base_url: "http://localhost:11434"
  embed_model: "nomic-embed-text"
  chat_model: "llama3.1:8b"

vector_store:
  persist_directory: "data/chroma"

graph_store:
  uri: "bolt://localhost:7687"
  username: "neo4j"
  password: "YOUR_NEO4J_PASSWORD"
  database: "neo4j"

ingestion:
  chunk_size: 1000
  chunk_overlap: 200
```

> **Note:** Replace `YOUR_NEO4J_PASSWORD` with the actual password. Do not publish a real password in a public repository. For a deployed application, use environment variables or a secret manager.

### Step 6 — Create `src/config.py`

This module loads YAML configuration and builds the project-root path. The other modules call `load_config()` instead of duplicating file-loading logic.

```python
from pathlib import Path
from typing import Any

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_DIR / "config.yaml"


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError(
            f"{CONFIG_PATH} must contain a YAML object"
        )

    return config
```

- `ROOT_DIR` finds the repository root based on the location of this file.
- `CONFIG_PATH` points to the root `config.yaml`.
- `load_config()` reads YAML, converts it to a Python dictionary, and checks that the top-level value is a mapping.

### Step 7 — Create `src/graph_store.py`

This module centralizes Neo4j connections and graph operations. The `GraphDatabase.driver` object connects Python to the local Neo4j instance.

```python
from neo4j import GraphDatabase

from src.config import load_config


def get_graph_driver():
    config = load_config()["graph_store"]

    return GraphDatabase.driver(
        config["uri"],
        auth=(config["username"], config["password"]),
    )


def verify_graph_connection() -> None:
    with get_graph_driver() as driver:
        driver.verify_connectivity()
        print("Connected to Neo4j.")
```

- `get_graph_driver()` reads the URI and credentials and returns a driver.
- `verify_graph_connection()` checks that Neo4j is reachable. The `with` block closes the driver when finished.

Connection check:

```powershell
.\.venv\Scripts\python.exe -c "from src.graph_store import verify_graph_connection; verify_graph_connection()"
```

### Step 8 — Create `src/vector_store.py`

This module opens the persistent Chroma collection and configures Ollama embeddings.

```python
def get_vector_store():
    config = load_config()
    persist_path = Path(
        config["vector_store"]["persist_directory"]
    )

    if not persist_path.is_absolute():
        persist_path = ROOT_DIR / persist_path

    persist_path.mkdir(parents=True, exist_ok=True)

    embeddings = OllamaEmbeddings(
        model=config["ollama"]["embed_model"],
        base_url=config["ollama"]["base_url"],
    )

    return Chroma(
        collection_name="wikipedia_articles",
        persist_directory=str(persist_path),
        embedding_function=embeddings,
    )


def add_documents(documents):
    if not documents:
        print("No document chunks to add.")
        return

    get_vector_store().add_documents(documents)
    print(f"Added {len(documents)} chunks to Chroma.")
```

- `get_vector_store()` resolves the Chroma directory, creates it if needed, configures the embedding model, and returns the collection.
- `add_documents()` stores document chunks and their metadata in Chroma. Chroma uses the configured embedding function to create vectors.

### Step 9 — Download Wikipedia Articles in `src/ingest.py`

The project selected six articles:

```text
Artificial intelligence
Machine learning
Large language model
Graph database
Vector database
Retrieval-augmented generation
```

The `fetch_article(title)` method requests plain text from the Wikipedia API, checks the HTTP response, parses JSON, extracts the article text, constructs a Wikipedia source URL, and returns a LangChain `Document`.

The returned document contains `page_content` for the article text and metadata including the title, topic, and source URL. A timeout is used so a stalled web request does not wait indefinitely.

### Step 10 — Split Articles into Chunks

The ingestion code uses `RecursiveCharacterTextSplitter` with `chunk_size` and `chunk_overlap` from configuration. The splitter makes smaller, overlapping documents from each article.

- Small chunks improve retrieval precision.
- Overlap helps retain context when a relevant sentence falls near a chunk boundary.
- Metadata such as the title and source URL is carried into the chunks.

### Step 11 — Store Chunks in Chroma and the Graph in Neo4j

Ingestion calls `add_documents(chunks)` to store the chunks in Chroma. It also executes parameterized Cypher through the Neo4j driver to create or reuse graph nodes and relationships.

```cypher
MERGE (article:Article {title: $title})
SET article.source = $source

MERGE (topic:Topic {name: $topic})
MERGE (article)-[:HAS_TOPIC]->(topic)

MERGE (chunk:Chunk {
    text: $text,
    source: $source,
    title: $title
})
MERGE (article)-[:HAS_CHUNK]->(chunk)
```

- `MERGE` reuses a matching node or relationship, creating it if it does not exist.
- `$title`, `$source`, and other values are parameters supplied separately from the Cypher string.
- The article is connected to its topic and to each of its text chunks.

Run ingestion from the repository root:

```powershell
.\.venv\Scripts\python.exe -m src.ingest
```

### Step 12 — Inspect the Graph Entirely from Python

A new `src/inspect_graph.py` script was created to print node counts, relationship counts, article-topic examples, and chunk previews. This allowed the graph to be inspected from PowerShell without using Neo4j Browser.

Run it with:

```powershell
.\.venv\Scripts\python.exe -m src.inspect_graph
```

The initial inspection showed:

| Label or relationship | Initial count |
|---|---:|
| Article nodes | 6 |
| Topic nodes | 6 |
| Chunk nodes | 514 |
| `HAS_TOPIC` relationships | 6 |
| `HAS_CHUNK` relationships | 514 |

These are the counts from the initial inspection. Topic nodes and relationships were subsequently expanded with shared-topic data, so the later graph may have different counts.

### Step 13 — Add and Test Article-Context Traversal

A `find_article_context(driver, title)` method was added to `src/graph_store.py`. It finds an Article by title and uses optional matches to retrieve its topics and chunks.

The query's graph paths are:

```text
Article -HAS_TOPIC-> Topic
Article -HAS_CHUNK-> Chunk
```

The method returns Neo4j records as ordinary Python dictionaries. A separate `src/test_article_context.py` script called the method for “Artificial intelligence” and printed the topics, number of chunks, and a chunk preview. This tested Neo4j traversal independently from Chroma.

### Step 14 — Add and Test Related-Article Traversal

A `find_related_articles(driver, title, limit=10)` method was added. It starts from an article, matches topics connected to it, then finds other articles connected to those same topic nodes. It excludes the starting article, collects shared-topic names, counts them, sorts results, and applies a limit.

At first, the original `HAS_TOPIC` links did not find related articles because each article had its own unique topic. This was an expected result: there were no shared topic nodes in the original graph.

### Step 15 — Add Shared Concepts

To make meaningful article-to-article paths, a `add_mentioned_topics(driver, title, topics)` method and a topic map were used to add `MENTIONS_TOPIC` relationships.

The method uses `UNWIND` to process a list of topic names and `MERGE` to create or reuse Topic nodes and relationships:

```cypher
MATCH (article:Article {title: $title})
UNWIND $topics AS topic_name
MERGE (topic:Topic {name: topic_name})
MERGE (article)-[:MENTIONS_TOPIC]->(topic)
```

The related-article query was adjusted to match both `HAS_TOPIC` and `MENTIONS_TOPIC`. The query then found related articles through shared concepts such as Retrieval, Vector, Machine learning, Artificial intelligence, and Neural network.

The topic map used in this learning stage is explicitly supplied by the program. It is not an automatic fact-extraction model; the chosen concepts should be reviewed for accuracy.

### Step 16 — Update `src/query.py` for Hybrid Retrieval

The query script first asks the user for a question. It then uses Chroma to retrieve four direct chunks and extracts unique article titles from their metadata.

```python
direct_results = vector_store.similarity_search_with_score(
    question,
    k=4,
)
```

Each returned item contains a document and a distance score. The title and source URL are read from document metadata. Duplicate article titles are removed while preserving their order.

For each matching title, Python calls `find_article_context()` and `find_related_articles()`. This makes Neo4j expand the Chroma result into article topics, chunks, and related articles.

The user-facing output is organized into:

- **Direct Chroma matches** — passages found through vector similarity.
- **Neo4j graph expansion** — article topics, chunk counts, and related article titles.

### Step 17 — Collect Evidence and Generate an Answer

The final version of `src/query.py` imports `ChatOllama`, `SystemMessage`, and `HumanMessage`. It gathers direct Chroma chunks and selected chunks from graph-retrieved articles, builds a context string, and sends the question and evidence to Ollama.

The system instruction tells the model to answer from supplied evidence, avoid inventing facts, cite article titles and URLs when available, and state when the evidence is insufficient. The chat call is:

```python
response = chat.invoke(messages)
print(response.content)
```

`temperature=0` makes generation more focused and less variable. Local generation can be slow, particularly with a large model, a long prompt, or a computer without a capable GPU. Limiting the amount of evidence or selecting a smaller model can reduce waiting time.

## 5. Tests and Commands Used

| Purpose | Command |
|---|---|
| Verify Neo4j connection | `.\.venv\Scripts\python.exe -c "from src.graph_store import verify_graph_connection; verify_graph_connection()"` |
| Download and index articles | `.\.venv\Scripts\python.exe -m src.ingest` |
| Inspect node and relationship counts | `.\.venv\Scripts\python.exe -m src.inspect_graph` |
| Test article-to-topic and article-to-chunk traversal | `.\.venv\Scripts\python.exe -m src.test_article_context` |
| Test related article traversal | `.\.venv\Scripts\python.exe -m src.test_related_articles` |
| Run the full retrieval and answer pipeline | `.\.venv\Scripts\python.exe -m src.query` |

## 6. The Observed End-to-End Behavior

For questions such as “Explain GraphRAG” and “What is the difference between AI and ML?”, Chroma returned semantically related chunks. Python extracted the article titles. Neo4j then found article context and related articles through shared-topic relationships. Ollama generated a response from the evidence assembled by the Python script.

One observed answer correctly described machine learning as a field within artificial intelligence and noted that the provided evidence did not establish every possible nuance. This illustrated the intended grounded-answer behavior.

## 7. How to Interpret the Retrieval Results

- **Chroma distance:** A ranking score for vector similarity; a smaller distance is generally a closer match for this configured store. It is not a truth score.
- **Graph relatedness:** Means two articles share a connected topic according to the graph model. It does not automatically mean their claims are equivalent.
- **Graph-expanded evidence:** Text retrieved by following Neo4j connections rather than by the original vector search.
- **Generated answer:** An LLM-written explanation based on the evidence passed to it. It should be checked against the cited source text.

## 8. Troubleshooting

### Neo4j Connection Failure

- Confirm that the Neo4j database instance is started in Neo4j Desktop.
- Confirm the URI, username, and password in `config.yaml`.
- Check the Bolt address in Desktop; the common local value is `bolt://localhost:7687`.
- Run the Python connection check before running ingestion or querying.

### Ollama Connection Failure

- Confirm Ollama is installed and running.
- Confirm the configured model is available with `ollama list`.
- Test the model with `ollama run MODEL_NAME "Reply with OK"`.
- Check the base URL in `config.yaml`.

### No Related Articles

- Confirm that the topic relationships were added to the same Neo4j database used by the query script.
- Confirm the related-article Cypher matches `MENTIONS_TOPIC` as well as `HAS_TOPIC`.
- Remember that the original six unique topic relationships alone do not connect one article to another.

### Slow Answer Generation

- Ollama answer generation is often the slowest pipeline stage.
- Reduce the number and length of graph-expanded chunks sent to the model.
- Use a smaller chat model if needed, while keeping the embedding model unchanged for an already indexed collection.
- Check CPU and memory usage while the model is generating.

## 9. Summary

The project keeps each technology focused on its strengths:

| Component | Main responsibility |
|---|---|
| Wikipedia API | Fetch source article text |
| Text splitter | Divide articles into retrieval-sized chunks |
| Ollama embedding model | Represent questions and chunks as vectors |
| Chroma | Find semantically similar chunks |
| Neo4j | Traverse articles, topics, chunks, and shared concepts |
| Python | Coordinate ingestion, retrieval, graph queries, and prompting |
| Ollama chat model | Generate an answer from supplied evidence |

```text
Wikipedia text → chunks → Chroma vectors
                       ↘ Neo4j article/topic/chunk graph

Question → Chroma retrieval → Neo4j expansion → Ollama answer
```
