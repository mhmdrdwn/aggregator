import logging
import numpy as np
from functools import lru_cache
from urllib.parse import urlparse

from .config import (
    SPACY_MODEL,
    SBERT_MODEL,
    NER_LABELS,
    NLP_TEXT_LIMIT,
    EMBEDDING_TEXT_LIMIT,
    DEDUP_THRESHOLD,
    DOMAIN_TO_NAME,
)

logger = logging.getLogger(__name__)


def _hostname(url: str) -> str:
    try:
        host = urlparse(url).hostname or ""
        return host.removeprefix("www.")
    except Exception:
        return ""


@lru_cache(maxsize=1)
def _spacy_model():
    import spacy
    return spacy.load(SPACY_MODEL)


@lru_cache(maxsize=1)
def _sbert_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(SBERT_MODEL)


def _canonical_source(article: dict) -> str:
    """Return a clean publisher name for an article dict.

    Priority:
    1. DOMAIN_TO_NAME map keyed by the article's URL hostname (most reliable)
    2. 'publisher' key — set by pipeline for Google News title-only entries
    3. 'sitename' — trafilatura-extracted site name
    4. hostname fallback
    """
    host = _hostname(article.get("url", ""))
    if host in DOMAIN_TO_NAME:
        return DOMAIN_TO_NAME[host]
    return article.get("publisher") or article.get("sitename") or host or "Ukjent"


def _ner(text: str) -> list[dict]:
    doc = _spacy_model()(text[:NLP_TEXT_LIMIT])
    return [
        {"text": ent.text, "label": ent.label_}
        for ent in doc.ents
        if ent.label_ in NER_LABELS
    ]


def process_articles(raw_articles: list[dict]) -> list[dict]:
    """Process a batch of raw trafilatura dicts — NER + embeddings in one shot."""
    valid = [a for a in raw_articles if a.get("text")]
    if not valid:
        return []

    # NER per article (spaCy has no batch API worth using here)
    entities_list = [_ner(a["text"]) for a in valid]

    # Encode all texts in a single SBERT batch
    texts = [
        f"{a.get('title', '')}. {a['text'][:EMBEDDING_TEXT_LIMIT]}"
        for a in valid
    ]
    embeddings = _sbert_model().encode(texts, batch_size=32, show_progress_bar=True)

    results = []
    for a, entities, embedding in zip(valid, entities_list, embeddings):
        results.append({
            "title": a.get("title", ""),
            "text": a["text"],
            "url": a.get("url", ""),
            "author": a.get("author", ""),
            "date": a.get("date") or a.get("published", ""),
            "source": _canonical_source(a),
            "entities": entities,
            "embedding": embedding.tolist(),
            "link_url": a.get("link_url"),
        })

    return results


def deduplicate(articles: list[dict], threshold: float = DEDUP_THRESHOLD) -> list[dict]:
    if not articles:
        return []

    from sklearn.metrics.pairwise import cosine_similarity

    embeddings = np.array([a["embedding"] for a in articles])
    sim = cosine_similarity(embeddings)

    keep: list[dict] = []
    seen: set[int] = set()

    for i, article in enumerate(articles):
        if i in seen:
            continue
        keep.append(article)
        for j in range(i + 1, len(articles)):
            if sim[i][j] > threshold:
                seen.add(j)

    return keep
