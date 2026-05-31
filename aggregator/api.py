import json
from pathlib import Path

import psycopg2
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from .config import DATABASE_URL, DOMAIN_TO_NAME

# Canonical set of source names we actively crawl — used to filter out junk
_KNOWN_SOURCES = frozenset(DOMAIN_TO_NAME.values())

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
    topic: str = Query(""),
    author: str = Query(""),
):
    offset = (page - 1) * limit

    # Content filters (source, topic, author, search) are OR-combined —
    # selecting NRK + Sport returns NRK articles OR sport articles.
    # Date filters are AND-combined and applied on top as hard boundaries.
    content_clauses: list = []
    content_params: list = []
    date_clauses:   list = []
    date_params:    list = []

    if source:
        sources = [s.strip() for s in source.split(",") if s.strip()]
        ph = ",".join(["%s"] * len(sources))
        content_clauses.append(f"source IN ({ph})")
        content_params.extend(sources)
    if q:
        terms = [t.strip() for t in q.split(",") if t.strip()]
        term_clauses = ["(title ILIKE %s OR body ILIKE %s)" for _ in terms]
        content_clauses.append(f"({' OR '.join(term_clauses)})")
        for t in terms:
            content_params.extend([f"%{t}%", f"%{t}%"])
    if topic:
        topics = [t.strip() for t in topic.split(",") if t.strip()]
        ph = ",".join(["%s"] * len(topics))
        content_clauses.append(f"topic IN ({ph})")
        content_params.extend(topics)
    if author:
        authors = [a.strip() for a in author.split(",") if a.strip()]
        ph = ",".join(["%s"] * len(authors))
        content_clauses.append(f"author IN ({ph})")
        content_params.extend(authors)
    if date_from:
        date_clauses.append("published_at >= %s")
        date_params.append(date_from)
    if date_to:
        date_clauses.append("published_at < (%s::date + interval '1 day')")
        date_params.append(date_to)

    all_clauses = []
    if content_clauses:
        all_clauses.append(f"({' OR '.join(content_clauses)})")
    all_clauses.extend(date_clauses)
    params = content_params + date_params
    where_sql = ("WHERE " + " AND ".join(all_clauses)) if all_clauses else ""

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
                SELECT id, url, title, body, author, published_at, source, entities, sentiment, sentiment_score, topic, image_url
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
        id_, url, title, body, author, published_at, source_, entities, sentiment, sentiment_score, topic, image_url = row
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
                "sentiment": sentiment,
                "sentiment_score": sentiment_score,
                "topic": topic,
                "image_url": image_url,
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


@app.get("/api/topics")
def list_topics():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT topic, COUNT(*) FROM articles WHERE topic IS NOT NULL GROUP BY topic ORDER BY COUNT(*) DESC"
            )
            return [{"topic": row[0], "count": row[1]} for row in cur.fetchall()]
    finally:
        conn.close()


@app.get("/api/sentiment-timeline")
def sentiment_timeline(
    source: str = Query(""),
    q: str = Query(""),
    date_from: str = Query(""),
    date_to: str = Query(""),
    topic: str = Query(""),
):
    where_clauses = ["sentiment IS NOT NULL", "published_at IS NOT NULL"]
    params: list = []

    if source:
        sources = [s.strip() for s in source.split(",") if s.strip()]
        ph = ",".join(["%s"] * len(sources))
        where_clauses.append(f"source IN ({ph})")
        params.extend(sources)
    if q:
        terms = [t.strip() for t in q.split(",") if t.strip()]
        term_clauses = ["(title ILIKE %s OR body ILIKE %s)" for _ in terms]
        where_clauses.append(f"({' OR '.join(term_clauses)})")
        for t in terms:
            params.extend([f"%{t}%", f"%{t}%"])
    if date_from:
        where_clauses.append("published_at >= %s")
        params.append(date_from)
    else:
        where_clauses.append("published_at >= NOW() - INTERVAL '7 days'")
    if date_to:
        where_clauses.append("published_at < (%s::date + interval '1 day')")
        params.append(date_to)
    if topic:
        topics = [t.strip() for t in topic.split(",") if t.strip()]
        ph = ",".join(["%s"] * len(topics))
        where_clauses.append(f"topic IN ({ph})")
        params.extend(topics)

    where_sql = "WHERE " + " AND ".join(where_clauses)

    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT DATE(published_at) AS day, sentiment, COUNT(*) AS cnt
                FROM articles
                {where_sql}
                GROUP BY day, sentiment
                ORDER BY day
                """,
                params,
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    by_date: dict = {}
    for day, sentiment, cnt in rows:
        key = day.isoformat()
        if key not in by_date:
            by_date[key] = {"date": key, "positive": 0, "negative": 0, "neutral": 0}
        if sentiment in by_date[key]:
            by_date[key][sentiment] = cnt

    return sorted(by_date.values(), key=lambda x: x["date"])


@app.get("/api/entity-timeline")
def entity_timeline(
    source: str = Query(""),
    topic: str = Query(""),
    label: str = Query(""),
):
    labels = [l.strip() for l in label.split(",") if l.strip()] or ["PER", "ORG", "GPE"]

    art_where = [
        "a.published_at >= NOW() - INTERVAL '7 days'",
        "a.entities IS NOT NULL",
        "jsonb_typeof(a.entities) = 'array'",
    ]
    art_params: list = []

    if source:
        sources = [s.strip() for s in source.split(",") if s.strip()]
        ph = ",".join(["%s"] * len(sources))
        art_where.append(f"a.source IN ({ph})")
        art_params.extend(sources)
    if topic:
        topics = [t.strip() for t in topic.split(",") if t.strip()]
        ph = ",".join(["%s"] * len(topics))
        art_where.append(f"a.topic IN ({ph})")
        art_params.extend(topics)

    label_sql = " OR ".join(["ent->>'label' = %s"] * len(labels))
    where_sql  = "WHERE " + " AND ".join(art_where) + f" AND ({label_sql})"

    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT ent->>'text' AS entity, COUNT(*) AS total
                FROM articles a, jsonb_array_elements(a.entities) AS ent
                {where_sql}
                GROUP BY entity
                HAVING COUNT(*) > 1
                ORDER BY total DESC
                LIMIT 8
                """,
                art_params + labels,
            )
            top_entities = [row[0] for row in cur.fetchall()]
            if not top_entities:
                return {"dates": [], "series": []}

            ent_ph = ",".join(["%s"] * len(top_entities))
            cur.execute(
                f"""
                SELECT DATE(a.published_at) AS day,
                       ent->>'text'          AS entity,
                       COUNT(*)              AS cnt
                FROM articles a, jsonb_array_elements(a.entities) AS ent
                {where_sql}
                  AND ent->>'text' IN ({ent_ph})
                GROUP BY day, entity
                ORDER BY day
                """,
                art_params + labels + top_entities,
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    all_dates: list = sorted({row[0].isoformat() for row in rows})
    by_entity: dict = {e: {} for e in top_entities}
    for day, entity, cnt in rows:
        if entity in by_entity:
            by_entity[entity][day.isoformat()] = cnt

    return {
        "dates": all_dates,
        "series": [
            {"entity": e, "values": [by_entity[e].get(d, 0) for d in all_dates]}
            for e in top_entities
            if any(by_entity[e].values())
        ],
    }


@app.get("/api/entity-aliases")
def entity_aliases():
    """Debug endpoint: show all active entity alias mappings (static + dynamic)."""
    from .nlp import _ENTITY_ALIASES, _dynamic_aliases
    static = [{"text": k[0], "label": k[1], "canonical": v, "source": "static"}
              for k, v in _ENTITY_ALIASES.items()]
    dynamic = [{"text": k[0], "label": k[1], "canonical": v, "source": "dynamic"}
               for k, v in _dynamic_aliases.items()]
    return {
        "static_count": len(static),
        "dynamic_count": len(dynamic),
        "aliases": static + dynamic,
    }


@app.get("/api/sources")
def list_sources():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT source, COUNT(*) FROM articles WHERE source IS NOT NULL GROUP BY source ORDER BY COUNT(*) DESC"
            )
            return [
                {"source": row[0], "count": row[1]}
                for row in cur.fetchall()
                if row[0] in _KNOWN_SOURCES
            ]
    finally:
        conn.close()


@app.get("/api/coverage")
def coverage(days: int = Query(14, ge=1, le=90)):
    """Per-source daily article counts for the last `days` days."""
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT source,
                       DATE(published_at) AS day,
                       COUNT(*)           AS cnt
                FROM   articles
                WHERE  published_at >= NOW() - INTERVAL '1 day' * %s
                  AND  source IS NOT NULL
                  AND  published_at IS NOT NULL
                GROUP  BY source, day
                ORDER  BY source, day
                """,
                (days,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    from datetime import date, timedelta
    today = date.today()
    date_range = [(today - timedelta(days=i)).isoformat() for i in range(days - 1, -1, -1)]

    by_source: dict = {}
    for source, day, cnt in rows:
        if source not in _KNOWN_SOURCES:
            continue
        if source not in by_source:
            by_source[source] = {}
        by_source[source][day.isoformat()] = cnt

    series = [
        {
            "source": src,
            "total": sum(by_date.values()),
            "daily": [by_date.get(d, 0) for d in date_range],
        }
        for src, by_date in sorted(by_source.items(), key=lambda x: -sum(x[1].values()))
    ]

    return {"dates": date_range, "series": series}


@app.get("/api/authors")
def list_authors(
    limit: int = Query(50, ge=1, le=200),
    source: str = Query(""),
    topic: str = Query(""),
    days: int = Query(7, ge=1, le=90),
):
    # Exclude wire services and editorial robots that are not individual journalists
    _NOISE = {"NTB", "N NTB", "NTB-Reuters", "Redaksjonen", "VG CNP-Live",
              "BTs bedriftsrobot", "BTs boligrobot", "ANB", "ANB-NTB"}

    where = [
        "author IS NOT NULL", "author != ''",
        f"published_at >= NOW() - INTERVAL '1 day' * {days}",
    ]
    params: list = []
    if source:
        where.append("source = %s")
        params.append(source)
    if topic:
        where.append("topic = %s")
        params.append(topic)

    where_sql = "WHERE " + " AND ".join(where)

    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT author, source, COUNT(*) AS cnt
                FROM articles
                {where_sql}
                GROUP BY author, source
                ORDER BY cnt DESC
                LIMIT %s
                """,
                params + [limit * 3],  # fetch extra to absorb noise filtering
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    # Aggregate per author across sources, skip noise
    from collections import defaultdict
    by_author: dict[str, dict] = defaultdict(lambda: {"count": 0, "sources": set()})
    for author, source_, cnt in rows:
        if author in _NOISE:
            continue
        by_author[author]["count"] += cnt
        if source_:
            by_author[author]["sources"].add(source_)

    result = sorted(by_author.items(), key=lambda x: -x[1]["count"])[:limit]
    return [
        {"author": a, "count": d["count"], "sources": sorted(d["sources"])}
        for a, d in result
    ]
