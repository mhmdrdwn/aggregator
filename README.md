# Norwegian News Aggregator

An open-source news aggregator for Norwegian media covering 60+ publishers. Crawls RSS feeds, news sitemaps, and Amedia homepages every 30 minutes — extracting full article text, running Norwegian NLP (NER, sentiment, topic classification, semantic deduplication), and surfacing everything through a filterable web UI.

## What it does

- **Discovers** articles from 60+ Norwegian publishers via RSS, news sitemaps, and Amedia CMS homepage crawling
- **Extracts** full article text and metadata using Trafilatura (fast path) with Scrapling/Playwright fallback for JS-heavy sites
- **Enriches** each article with named entities, sentiment score, topic label, and a 768-dim sentence embedding
- **Deduplicates** semantically similar articles (cosine similarity > 0.92) before saving
- **Backfills** existing articles missing enrichment on every scheduler cycle
- **Serves** a single-page web UI with article search, filtering, treemap charts, and analytics

## Tech stack

| Layer | Tool |
|---|---|
| Discovery | feedparser (RSS), requests (sitemaps + Amedia homepages) |
| Extraction | Trafilatura (primary), Scrapling + Playwright (JS fallback) |
| NLP — NER | spaCy `nb_core_news_lg` (Norwegian NorNE labels) |
| NLP — Embeddings | `NbAiLab/nb-sbert-base` (768-dim sentence vectors) |
| NLP — Sentiment | `cardiffnlp/twitter-xlm-roberta-base-sentiment` |
| NLP — Topics | Keyword scoring + SBERT cosine fallback (12 topics) |
| Deduplication | Cosine similarity on SBERT embeddings (threshold 0.92) |
| Storage | PostgreSQL + pgvector |
| API | FastAPI |
| Frontend | Vanilla JS + D3.js v7 |

## Project structure

```
aggregator/
├── aggregator/
│   ├── config.py       — feed lists, publisher registry, NLP constants, skip patterns
│   ├── discovery.py    — RSS / sitemap / Amedia homepage crawlers
│   ├── extraction.py   — Trafilatura fast path + Scrapling/Playwright fallback
│   ├── nlp.py          — NER, entity normalisation, SBERT embeddings, sentiment,
│   │                     topic classification, cosine deduplication
│   ├── storage.py      — PostgreSQL read/write (upsert with COALESCE backfill)
│   ├── pipeline.py     — orchestrates discovery → fetch → NLP → dedup → save
│   ├── scheduler.py    — runs pipeline + backfill on a configurable interval
│   ├── api.py          — FastAPI endpoints (articles, entities, topics, authors, …)
│   └── templates/
│       └── index.html  — single-page UI (D3 treemaps, sentiment timeline, filters)
├── main.py             — CLI entry point
├── schema.sql          — DB schema (applied automatically via Docker)
├── docker-compose.yml  — Postgres + pgvector container
└── requirements.txt
```

## Publisher coverage

**~60 Norwegian publishers** across three ingestion methods:

| Method | Publishers |
|---|---|
| RSS feeds | NRK, VG, TV2, Aftenposten, Dagsavisen, E24, Digi.no, Bergens Tidende, Stavanger Aftenblad, Fædrelandsvennen, Adresseavisen, Sunnmørsposten, Romsdals Budstikke, iTromsø, Harstad Tidende, Agderposten, Varden, Sunnhordland, Innherred, Trønderbladet, Avisa Sør-Trøndelag, Altaposten, Folkebladet, Framtid i Nord, Teknisk Ukeblad, Filter Nyheter, Morgenbladet, Hallingdølen |
| News sitemaps | Dagbladet, Dagens Næringsliv, Vårt Land, Dagen, Shifter, ABC Nyheter |
| Amedia homepage | Nettavisen, Romerikes Blad, Budstikka, Drammens Tidende, Moss Avis, Tønsbergs Blad, Fredriksstad Blad, Halden Arbeiderblad, Haugesunds Avis, Telemarksavisa, Avisa Nordland, Bladet Vesterålen, Lofotposten, Fremover, Namdalsavisa, Oppland Arbeiderblad, Gudbrandsdølen Dagningen, Nordlys, Trønder-Avisa, Hamar Arbeiderblad, Rana Blad, Nationen, Glåmdalen, Østlendingen, Nidaros, Steinkjer-Avisa |

## Database schema

```sql
articles (
    id              SERIAL PRIMARY KEY,
    url             TEXT UNIQUE,
    title           TEXT,
    body            TEXT,
    author          TEXT,
    published_at    TIMESTAMP,
    source          TEXT,
    embedding       vector(768),   -- NbAiLab/nb-sbert-base
    cluster_id      INTEGER,
    entities        JSONB,         -- [{text, label}, …]  NorNE labels
    sentiment       TEXT,          -- positive / negative / neutral
    sentiment_score NUMERIC(5,3),
    topic           TEXT,          -- one of 12 topic labels
    link_url        TEXT,          -- original link (before redirect)
    image_url       TEXT,          -- og:image extracted from article page
    created_at      TIMESTAMP
)
```

Indexes: `ivfflat` on embedding (cosine), B-tree on `published_at` and `source`.

## NLP pipeline

### Named entity recognition
Uses spaCy `nb_core_news_lg` with Norwegian NorNE labels (`PER`, `ORG`, `GPE_LOC`, `GPE_ORG`, `LOC`, `EVT`). Entities go through a two-stage normalisation pipeline before storage:

1. **Static alias table** — ~60 hand-curated entries for known figures, transliteration variants (`Zelenskyj/Zelensky`), Norwegian genitive forms (`Norges → Norge`, `Putins → Vladimir Putin`), and common organisations.
2. **Per-article co-occurrence merging** — if `«Warholm»` (single-token PER) and `«Karsten Warholm»` (multi-token PER) both appear in the same article, the short form is absorbed into the full name. Ambiguous cases (two full names sharing the same last token) are left unchanged.
3. **Corpus suffix-matching** — after each pipeline run, entity frequencies are queried from the DB. Single-token entities that unambiguously match the last token of exactly one high-frequency multi-token entity (≥ 20 articles) are added to a dynamic alias cache (`_dynamic_aliases`). This means new public figures are absorbed automatically once they accumulate enough coverage — no code change required. The debug endpoint `GET /api/entity-aliases` lists all active static and dynamic aliases.

### Topic classification
12 topics: `sport`, `kriminalitet`, `politikk`, `økonomi`, `helse`, `teknologi`, `klima`, `kultur`, `utenriks`, `forsvar`, `utdanning`, `samfunn`. Primary method is keyword scoring against title + body; falls back to SBERT cosine similarity against topic anchor embeddings when no keyword scores ≥ 2.

### Sentiment
`cardiffnlp/twitter-xlm-roberta-base-sentiment` run on title + first 300 characters of body. Labels mapped to `positive` / `negative` / `neutral`.

### Deduplication
Cosine similarity matrix over SBERT embeddings. Articles with similarity > 0.92 to an already-kept article are dropped before saving.

## Web UI

Single-page app served at `http://localhost:8000`. Features:

- **Article feed** — paginated, filterable by source, topic, author, date range, and free-text search
- **Entities tab** — treemap of most-mentioned named entities (filterable by label: PER/ORG/GPE)
- **Topics tab** — treemap of topic distribution
- **Journalister tab** — treemap of most-published authors (click to filter articles)
- **Sentiment timeline** — stacked bar chart of positive/negative/neutral per day
- **Entity timeline** — line chart of top-8 entity mentions over the past 7 days
- **Coverage chart** — per-source article counts heatmap for the past 14 days

## Quickstart

```bash
# 1. Start the database
docker compose up -d

# 2. Set up Python environment
python -m venv aggregator-env && source aggregator-env/bin/activate
pip install -r requirements.txt
python -m spacy download nb_core_news_lg

# 3. Configure environment
cp .env.example .env   # uses port 5434 (avoids Cursor/VS Code Postgres on 5432)

# 4. Run the pipeline once to test
python main.py --once

# 5. Start the web UI (separate terminal)
python main.py --serve

# 6. Run on schedule (every 30 min, includes automatic backfill)
python main.py
```

## CLI

```
python main.py                    # scheduler — pipeline every 30 min
python main.py --once             # single pipeline run, then exit
python main.py --serve            # web UI on http://localhost:8000
python main.py --backfill         # re-enrich articles missing sentiment/entities/topic
python main.py --backfill-images  # fetch og:image for articles that have none
python main.py --backfill-entities # re-normalize stored entities with current alias tables
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | — | PostgreSQL connection string (required) |
| `SCHEDULE_INTERVAL_MINUTES` | `30` | Pipeline run interval |

All publisher lists, NLP model names, skip-URL patterns, and deduplication threshold are in `aggregator/config.py`.

## License

Copyright (c) 2026 Mohamed Radwan. All rights reserved.

Free for personal, educational, and evaluation use. Commercial use — including incorporating this software into a paid product or service — requires prior written permission. See [LICENSE](LICENSE) for full terms or contact **mohamed@uppercase.no** for commercial licensing.

## API endpoints

| Endpoint | Description |
|---|---|
| `GET /api/articles` | Paginated article list. Filters: `source`, `q`, `date_from`, `date_to`, `topic`, `page`, `limit` |
| `GET /api/entities` | Top named entities by mention count. Filters: `source`, `label` |
| `GET /api/topics` | Topic distribution across all articles |
| `GET /api/authors` | Most-published authors. Filters: `source`, `topic`, `days` |
| `GET /api/sources` | Article counts per source |
| `GET /api/coverage` | Per-source daily article counts for the last N days (default 14) |
| `GET /api/sentiment-timeline` | Daily positive/negative/neutral counts. Filters: `source`, `q`, `topic`, `date_from`, `date_to` |
| `GET /api/entity-timeline` | Daily mention counts for top-8 entities over the last 7 days |
| `GET /api/entity-aliases` | Debug: all active entity alias mappings (static + dynamic) with counts |
