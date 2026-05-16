import logging

from .discovery import discover_all
from .extraction import fetch_article
from .nlp import deduplicate, process_articles
from .storage import article_exists, get_unenriched_articles, save_article

logger = logging.getLogger(__name__)


def run_pipeline() -> None:
    logger.info("Pipeline started")

    discovered = discover_all()

    new_items = [item for item in discovered if not article_exists(item["url"])]
    logger.info(f"{len(new_items)} new URLs to process (skipping {len(discovered) - len(new_items)} already in DB)")

    # Step 1: fetch all articles
    raw_articles: list[dict] = []
    for item in new_items:
        article_data = fetch_article(item["url"])
        if article_data:
            raw_articles.append(article_data)

    logger.info(f"Fetched {len(raw_articles)} articles — running NLP batch")

    # Step 2: NER + embeddings in one batch (much faster than one-at-a-time)
    processed = process_articles(raw_articles)
    logger.info(f"Processed {len(processed)} articles")

    unique_articles = deduplicate(processed)
    logger.info(f"After deduplication: {len(unique_articles)} articles")

    for article in unique_articles:
        try:
            save_article(article)
        except Exception as e:
            logger.error(f"Failed to save {article.get('url')}: {e}")

    logger.info("Pipeline complete")


def run_backfill(batch_size: int = 100) -> None:
    """Re-enrich articles in the DB that are missing sentiment/entities/topic.

    Uses stored body — no HTTP fetching, so it never hits rate limits or
    search-page URLs that were saved as link_url fallbacks.
    """
    logger.info("Backfill started")

    total_done = 0
    while True:
        items = get_unenriched_articles(batch_size)
        if not items:
            break

        logger.info(f"Backfill batch: {len(items)} articles to re-enrich from DB body")

        processed = process_articles(items)
        for article in processed:
            try:
                save_article(article)
            except Exception as e:
                logger.error(f"Backfill failed to save {article.get('url')}: {e}")

        total_done += len(processed)
        logger.info(f"Backfill progress: {total_done} articles enriched so far")

    logger.info(f"Backfill complete — {total_done} articles enriched")
