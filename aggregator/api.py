import json
from pathlib import Path

import psycopg2
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from .config import DATABASE_URL

app = FastAPI(title="Norwegian News Aggregator")

_TEMPLATE = Path(__file__).parent / "templates" / "index.html"


@app.get("/", response_class=HTMLResponse)
def index():
    return _TEMPLATE.read_text()


@app.get("/api/articles")
def list_articles(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    source: str = Query(""),
    q: str = Query(""),
):
    offset = (page - 1) * limit

    where_clauses = []
    params: list = []

    if source:
        where_clauses.append("source = %s")
        params.append(source)
    if q:
        where_clauses.append("(title ILIKE %s OR body ILIKE %s)")
        params.extend([f"%{q}%", f"%{q}%"])

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT COUNT(*) FROM articles {where_sql}
                """,
                params,
            )
            total = cur.fetchone()[0]

            cur.execute(
                f"""
                SELECT id, url, title, body, author, published_at, source, entities
                FROM articles
                {where_sql}
                ORDER BY published_at DESC NULLS LAST, created_at DESC
                LIMIT %s OFFSET %s
                """,
                params + [limit, offset],
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    articles = []
    for row in rows:
        id_, url, title, body, author, published_at, source_, entities = row
        articles.append(
            {
                "id": id_,
                "url": url,
                "title": title,
                "snippet": (body or "")[:200].strip(),
                "author": author,
                "published_at": published_at.isoformat() if published_at else None,
                "source": source_,
                "entities": entities if isinstance(entities, list) else [],
            }
        )

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": max(1, -(-total // limit)),
        "articles": articles,
    }


@app.get("/api/sources")
def list_sources():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT source, COUNT(*) FROM articles WHERE source IS NOT NULL GROUP BY source ORDER BY COUNT(*) DESC"
            )
            return [{"source": row[0], "count": row[1]} for row in cur.fetchall()]
    finally:
        conn.close()
