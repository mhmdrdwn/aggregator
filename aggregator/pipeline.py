import logging

from .discovery import discover_all
from .extraction import fetch_article
from .nlp import deduplicate, process_articles
from .storage import article_exists, save_article

logger = logging.getLogger(__name__)


def run_pipeline() -> None:
    logger.info("Pipeline started")

    discovered = discover_all()

    new_items = [item for item in discovered if not article_exists(item["url"])]
    logger.info(f"{len(new_items)} new URLs to process (skipping {len(discovered) - len(new_items)} known)")

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
