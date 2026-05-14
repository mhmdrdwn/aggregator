CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS articles (
    id           SERIAL PRIMARY KEY,
    url          TEXT UNIQUE NOT NULL,
    title        TEXT,
    body         TEXT,
    author       TEXT,
    published_at TIMESTAMP,
    source       TEXT,
    embedding    vector(768),
    cluster_id   INTEGER,
    entities     JSONB,
    created_at   TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS articles_embedding_idx
    ON articles USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS articles_published_at_idx ON articles (published_at DESC);
CREATE INDEX IF NOT EXISTS articles_source_idx ON articles (source);
