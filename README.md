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
    entities        JSONB,         -- [{text, label}, …]  NorNE labels
    sentiment       TEXT,          -- positive / negative / neutral
    sentiment_score NUMERIC(5,3),
    topic           TEXT,          -- one of 12 topic labels
    link_url        TEXT,          -- original link (before redirect)
    created_at      TIMESTAMP
)
```

Indexes: `ivfflat` on embedding (cosine), B-tree on `published_at` and `source`.

## NLP pipeline

### Named entity recognition
Uses spaCy `nb_core_news_lg` with Norwegian NorNE labels (`PER`, `ORG`, `GPE_LOC`, `GPE_ORG`, `LOC`, `EVT`). Entities are normalised (genitive-s stripping, alias table for common figures and places) and deduplicated within each article before storage.

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
cp .env.example .env   # set DATABASE_URL if different from default

# 4. Run the pipeline once to test
python main.py --once

# 5. Start the web UI (separate terminal)
python main.py --serve

# 6. Run on schedule (every 30 min, includes automatic backfill)
python main.py
```

## CLI

```
python main.py              # scheduler — pipeline + backfill every 30 min
python main.py --once       # single pipeline run, then exit
python main.py --serve      # web UI on http://localhost:8000
python main.py --backfill   # re-enrich articles missing sentiment/entities/topic
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | — | PostgreSQL connection string (required) |
| `SCHEDULE_INTERVAL_MINUTES` | `30` | Pipeline run interval |

All publisher lists, NLP model names, skip-URL patterns, and deduplication threshold are in `aggregator/config.py`.
