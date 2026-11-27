"""
Create an interactive HTML ingestion report.

The report is generated automatically after the Wikipedia ingestion
process updates Chroma and Neo4j.

It provides four plain-language views:
1. Chunks created for each article.
2. Types of data stored in Neo4j.
3. Connections between the stored graph items.
4. Distribution of text-chunk lengths.

Output: docs/ingestion-statistics.html
"""
from html import escape
from pathlib import Path

import plotly.graph_objects as go

from src.config import ROOT_DIR, load_config
from src.graph_store import get_graph_driver


NODE_LABELS = {
    "Article": "Wikipedia articles",
    "Topic": "Topics",
    "Chunk": "Text chunks",
}

RELATIONSHIP_LABELS = {
    "HAS_TOPIC": "Article-to-topic links",
    "HAS_CHUNK": "Article-to-text links",
    "MENTIONS_TOPIC": "Article-to-concept links",
}


def _make_bar_chart(
    *,
    title: str,
    labels: list[str],
    values: list[int],
    x_title: str,
    color: str,
) -> go.Figure:
    figure = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=color,
            text=values,
            textposition="outside",
            hovertemplate=(
                "<b>%{y}</b><br>"
                + x_title
                + ": %{x}"
                + "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        title={
            "text": title,
            "x": 0.02,
            "xanchor": "left",
        },
        height=max(360, 90 + len(labels) * 48),
        margin={"l": 230, "r": 50, "t": 70, "b": 60},
        template="plotly_white",
        showlegend=False,
        font={"size": 14},
        xaxis_title=x_title,
        yaxis_title="",
    )
    figure.update_yaxes(autorange="reversed")
    figure.update_xaxes(rangemode="tozero")

    return figure


def _make_chunk_length_chart(
    chunk_lengths: list[int],
) -> go.Figure:
    figure = go.Figure(
        go.Histogram(
            x=chunk_lengths,
            nbinsx=20,
            marker_color="#00A884",
            hovertemplate=(
                "Chunk length range: %{x}<br>"
                "Number of chunks in this range: %{y}"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        title={
            "text": "How long are the stored text chunks?",
            "x": 0.02,
            "xanchor": "left",
        },
        height=400,
        margin={"l": 80, "r": 50, "t": 70, "b": 70},
        template="plotly_white",
        showlegend=False,
        font={"size": 14},
        xaxis_title="Characters in a chunk",
        yaxis_title="No. of chunks in this length range",
    )

    return figure


def create_ingestion_report() -> Path:
    config = load_config()
    database = config["graph_store"].get("database", "neo4j")

    with get_graph_driver() as driver:
        article_records, _, _ = driver.execute_query(
            """
            MATCH (article:Article)-[:HAS_CHUNK]->(chunk:Chunk)
            RETURN article.title AS title,
                   count(chunk) AS chunk_count
            ORDER BY chunk_count DESC, title
            """,
            database_=database,
        )

        node_records, _, _ = driver.execute_query(
            """
            MATCH (node)
            UNWIND labels(node) AS label
            RETURN label, count(*) AS count
            ORDER BY label
            """,
            database_=database,
        )

        relationship_records, _, _ = driver.execute_query(
            """
            MATCH ()-[relationship]->()
            RETURN type(relationship) AS type,
                   count(*) AS count
            ORDER BY type
            """,
            database_=database,
        )

        chunk_length_records, _, _ = driver.execute_query(
            """
            MATCH (chunk:Chunk)
            WHERE chunk.text IS NOT NULL
            RETURN size(chunk.text) AS character_count
            """,
            database_=database,
        )

    article_data = [record.data() for record in article_records]
    node_data = [record.data() for record in node_records]
    relationship_data = [
        record.data() for record in relationship_records
    ]
    chunk_lengths = [
        record["character_count"]
        for record in chunk_length_records
    ]

    if not article_data:
        raise RuntimeError(
            "No article chunks were found in Neo4j. "
            "Run ingestion before creating the report."
        )

    node_counts = {
        record["label"]: record["count"]
        for record in node_data
    }
    relationship_counts = {
        record["type"]: record["count"]
        for record in relationship_data
    }

    article_labels = [
        record["title"] for record in article_data
    ]
    article_counts = [
        record["chunk_count"] for record in article_data
    ]

    readable_node_labels = [
        NODE_LABELS.get(label, label)
        for label in node_counts
    ]
    readable_node_counts = list(node_counts.values())

    readable_relationship_labels = [
        RELATIONSHIP_LABELS.get(name, name)
        for name in relationship_counts
    ]
    readable_relationship_counts = list(
        relationship_counts.values()
    )

    total_articles = node_counts.get("Article", 0)
    total_topics = node_counts.get("Topic", 0)
    total_chunks = node_counts.get("Chunk", 0)
    total_relationships = sum(relationship_counts.values())

    charts = [
        (
            _make_bar_chart(
                title="How many text chunks were created for each article?",
                labels=article_labels,
                values=article_counts,
                x_title="Text chunks",
                color="#5965E9",
            ),
            """
            <p>
              Each bar represents one Wikipedia article. Its length shows
              how many text pieces were created from that article during
              ingestion. More pieces usually mean the source article
              contained more text.
            </p>
            """,
        ),
        (
            _make_bar_chart(
                title="What information is stored in the graph?",
                labels=readable_node_labels,
                values=readable_node_counts,
                x_title="Stored items",
                color="#F05A3A",
            ),
            """
            <p>
              These bars count the things Neo4j stores: Wikipedia articles,
              topics, and text chunks. A text chunk is a small piece of an
              article that the system can retrieve later.
            </p>
            """,
        ),
        (
            _make_bar_chart(
                title="How are the stored items connected?",
                labels=readable_relationship_labels,
                values=readable_relationship_counts,
                x_title="Connections",
                color="#8A54C8",
            ),
            """
            <p>
              These bars count links between stored items. For example,
              an article-to-text link connects an article to one of its
              chunks. A larger number means more links of that type; it
              does not mean there are more articles.
            </p>
            <p>
              Article-to-concept links come from the project's configured
              topic associations. They describe the graph data entered by
              this project and are not, by themselves, proof that two
              articles make the same claim.
            </p>
            """,
        ),
        (
            _make_chunk_length_chart(chunk_lengths),
            """
            <p>
              The horizontal axis groups text chunks by their approximate
              length in characters. The vertical axis shows how many chunks
              fall into each length range. This helps check whether ingestion
              created chunks that are reasonably sized. It does not measure
              answer quality or whether a chunk is relevant to a question.
            </p>
            """,
        ),
    ]

    chart_html = []

    for index, (figure, explanation) in enumerate(charts):
        plot_html = figure.to_html(
            full_html=False,
            include_plotlyjs=True if index == 0 else False,
            config={"responsive": True},
        )

        chart_html.append(
            f"""
            <section class="chart-section">
              <div class="explanation">
                {explanation}
              </div>
              {plot_html}
            </section>
            """
        )

    output_path = (
        ROOT_DIR / "outputs" / "ingestion-statistics.html"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Wikipedia GraphRAG Ingestion Statistics</title>
  <style>
    :root {{
      color-scheme: light;
      font-family: Arial, Helvetica, sans-serif;
      color: #202733;
      background: #f5f7fa;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      padding: 32px 20px;
    }}

    main {{
      max-width: 1100px;
      margin: 0 auto;
    }}

    header {{
      margin-bottom: 28px;
    }}

    h1 {{
      margin: 0 0 12px;
      color: #17365d;
      font-size: 2rem;
    }}

    header p {{
      max-width: 760px;
      margin: 0;
      color: #4b5563;
      line-height: 1.65;
    }}

    .summary {{
      display: grid;
      grid-template-columns: repeat(
        auto-fit,
        minmax(160px, 1fr)
      );
      gap: 14px;
      margin: 24px 0 32px;
    }}

    .summary-card {{
      padding: 18px;
      border: 1px solid #dce3ec;
      border-radius: 10px;
      background: #ffffff;
    }}

    .summary-card strong {{
      display: block;
      margin-bottom: 6px;
      color: #17365d;
      font-size: 1.6rem;
    }}

    .summary-card span {{
      color: #4b5563;
      font-size: 0.95rem;
    }}

    .chart-section {{
      margin: 0 0 28px;
      padding: 22px;
      border: 1px solid #dce3ec;
      border-radius: 10px;
      background: #ffffff;
      box-shadow: 0 2px 8px rgba(20, 40, 70, 0.04);
    }}

    .explanation {{
      max-width: 850px;
      margin: 0 0 10px;
      color: #374151;
      font-size: 1rem;
      line-height: 1.7;
    }}

    .explanation p {{
      margin: 0 0 10px;
    }}

    .chart-section .plotly-graph-div {{
      width: 100% !important;
    }}

    footer {{
      margin-top: 24px;
      color: #606b78;
      font-size: 0.9rem;
      line-height: 1.6;
    }}

    @media (max-width: 600px) {{
      body {{
        padding: 18px 10px;
      }}

      .chart-section {{
        padding: 14px 8px;
      }}

      h1 {{
        font-size: 1.6rem;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Wikipedia GraphRAG Ingestion Statistics</h1>
      <p>
        This report summarizes what the ingestion process loaded into the
        project. Ingestion downloads Wikipedia text, divides it into chunks,
        and stores the content and its connections for later question
        answering.
      </p>
    </header>

    <section class="summary" aria-label="Ingestion totals">
      <div class="summary-card">
        <strong>{total_articles:,}</strong>
        <span>Wikipedia articles</span>
      </div>
      <div class="summary-card">
        <strong>{total_topics:,}</strong>
        <span>Topics in the graph</span>
      </div>
      <div class="summary-card">
        <strong>{total_chunks:,}</strong>
        <span>Text chunks in the graph</span>
      </div>
      <div class="summary-card">
        <strong>{total_relationships:,}</strong>
        <span>Connections in the graph</span>
      </div>
    </section>

    {''.join(chart_html)}

    <footer>
      <p>
        These statistics describe the current Neo4j database. They are
        refreshed when the ingestion process creates this report. Chunk
        counts and graph connections describe stored data; they do not
        measure answer accuracy.
      </p>
    </footer>
  </main>
</body>
</html>
"""

    output_path.write_text(page, encoding="utf-8")
    return output_path


if __name__ == "__main__":
    report_path = create_ingestion_report()
    print(f"Ingestion statistics report created: {report_path}")