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
    date_from: str = Query(""),
    date_to: str = Query(""),
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
    if date_from:
        where_clauses.append("published_at >= %s")
        params.append(date_from)
    if date_to:
        where_clauses.append("published_at < (%s::date + interval '1 day')")
        params.append(date_to)

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
                SELECT id, url, title, body, author, published_at, source, entities, link_url
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
        id_, url, title, body, author, published_at, source_, entities, link_url = row
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


@app.get("/api/entities")
def list_entities(
    source: str = Query(""),
    label: str = Query(""),
    limit: int = Query(80, ge=1, le=200),
):
    where = ["entities IS NOT NULL", "jsonb_typeof(entities) = 'array'"]
    params: list = []

    if source:
        where.append("source = %s")
        params.append(source)
    if label:
        where.append("ent->>'label' = %s")
        params.append(label)

    where_sql = "WHERE " + " AND ".join(where)

    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT ent->>'text' AS text,
                       ent->>'label' AS label,
                       COUNT(*)      AS count
                FROM   articles,
                       jsonb_array_elements(entities) AS ent
                {where_sql}
                GROUP  BY ent->>'text', ent->>'label'
                HAVING COUNT(*) > 1
                ORDER  BY count DESC
                LIMIT  %s
                """,
                params + [limit],
            )
            return [{"text": r[0], "label": r[1], "count": r[2]} for r in cur.fetchall()]
    finally:
        conn.close()


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
