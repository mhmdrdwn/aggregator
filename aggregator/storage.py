import json
import logging
from contextlib import contextmanager

import psycopg2

from .config import DATABASE_URL

logger = logging.getLogger(__name__)


@contextmanager
def _conn():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def save_article(article: dict) -> None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO articles
                    (url, title, body, author, published_at, source, embedding, entities, link_url,
                     sentiment, sentiment_score, topic)
                VALUES (%s, %s, %s, %s, %s, %s, %s::vector, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO UPDATE SET
                    sentiment       = COALESCE(articles.sentiment,       EXCLUDED.sentiment),
                    sentiment_score = COALESCE(articles.sentiment_score, EXCLUDED.sentiment_score),
                    topic           = COALESCE(articles.topic,           EXCLUDED.topic),
                    entities        = COALESCE(articles.entities,        EXCLUDED.entities)
                """,
                (
                    article["url"],
                    article["title"],
                    article["text"],
                    article.get("author"),
                    article.get("date") or None,
                    article.get("source"),
                    json.dumps(article["embedding"]),
                    json.dumps(article.get("entities", [])),
                    article.get("link_url"),
                    article.get("sentiment"),
                    article.get("sentiment_score"),
                    article.get("topic"),
                ),
            )


def find_similar_articles(embedding: list[float], limit: int = 10) -> list[tuple]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT url, title, source, published_at,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM articles
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (json.dumps(embedding), json.dumps(embedding), limit),
            )
            return cur.fetchall()


def article_exists(url: str) -> bool:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM articles WHERE url = %s", (url,))
            return cur.fetchone() is not None


def article_needs_enrichment(url: str) -> bool:
    """True if the article is in the DB but is missing NLP-derived fields."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM articles WHERE url = %s AND sentiment IS NULL",
                (url,),
            )
            return cur.fetchone() is not None


def get_unenriched_articles(batch_size: int = 100) -> list[dict]:
    """Return articles missing sentiment, with their stored body so we don't re-fetch."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT url, title, body, source, author, published_at
                FROM articles
                WHERE sentiment IS NULL
                  AND body IS NOT NULL AND body != ''
                ORDER BY published_at DESC NULLS LAST
                LIMIT %s
                """,
                (batch_size,),
            )
            cols = ["url", "title", "text", "source", "author", "date"]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
