# Norwegian News Aggregator

A lightweight, open-source news aggregator for Norwegian media. Topic-based discovery across open-access sources, with NLP clustering and no dependency on Opoint.

## Tech Stack

| Layer | Tool | Purpose |
|---|---|---|
| Discovery | feedparser + trafilatura | RSS + sitemap parsing |
| Fetching | Scrapling | Anti-bot bypass |
| Extraction | Trafilatura | Article body + metadata |
| NLP | spaCy (nb_core_news_lg) | Norwegian language processing |
| Clustering | sentence-transformers | Topic grouping |
| Storage | PostgreSQL + pgvector | Articles + embeddings |

## Project Structure

```
aggregator/
├── aggregator/
│   ├── config.py       — feed lists, env vars, constants
│   ├── discovery.py    — RSS parsing + sitemap discovery
│   ├── extraction.py   — Trafilatura (fast) + Scrapling (fallback)
│   ├── nlp.py          — spaCy NER, SBERT embeddings, deduplication
│   ├── storage.py      — PostgreSQL + pgvector read/write
│   ├── pipeline.py     — orchestrates all phases per run
│   └── scheduler.py    — runs pipeline on a cron interval
├── main.py             — CLI entry point
├── schema.sql          — DB schema (auto-runs via Docker)
├── docker-compose.yml  — Postgres + pgvector container
├── requirements.txt
└── .env.example
```

## Quickstart

```bash
# 1. Start the database (schema.sql is applied automatically)
docker compose up -d

# 2. Set up the Python environment
python -m venv aggregator-env && source aggregator-env/bin/activate
pip install -r requirements.txt
python -m spacy download nb_core_news_lg

# 3. Configure environment
cp .env.example .env
# Edit .env if your database credentials differ

# 4. Run once to test
python main.py --once

# 5. Run on schedule (every 30 min by default)
python main.py
```

## Configuration

All settings are controlled via environment variables (see `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | — | PostgreSQL connection string (required) |
| `MAX_ARTICLES_PER_RUN` | `50` | Articles fetched per pipeline run |
| `SCHEDULE_INTERVAL_MINUTES` | `30` | How often the scheduler runs |

## Norwegian NLP Models

| Model | Use case |
|---|---|
| `nb_core_news_lg` (spaCy) | NER, POS tagging, dependency parsing |
| `NbAiLab/nb-sbert-base` | Sentence embeddings, semantic similarity |
| `NbAiLab/nb-bert-base` | Text classification, fine-tuning |

## Milestones

| Week | Goal |
|---|---|
| 1 | Discovery working for 10 sources, articles saved to DB |
| 2 | Extraction stable, Scrapling fallback working |
| 3 | Norwegian NLP + basic topic clustering |
| 4 | Deduplication + simple API endpoint |
| 5–6 | Scale to 50+ sources, tune clustering quality |
