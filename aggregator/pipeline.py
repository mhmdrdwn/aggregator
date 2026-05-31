import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from .discovery import discover_all
from .extraction import fetch_article, _parse
from .nlp import deduplicate, normalize_entities, process_articles, refresh_corpus_aliases
from .storage import article_exists, get_articles_with_entities, get_articles_without_images, get_top_entities, get_unenriched_articles, save_article, set_image_url, update_entities
from .config import SKIP_URL_PATTERNS

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

    refresh_corpus_aliases(get_top_entities())
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


def run_entity_normalization_backfill(batch_size: int = 500) -> None:
    """Re-normalize stored entities for all articles using current alias tables.

    Builds corpus aliases first, then applies normalize_entities() to every
    article's stored entity list and writes the result back — no HTTP fetching,
    no model inference.
    """
    logger.info("Entity normalization backfill started — building corpus aliases")
    refresh_corpus_aliases(get_top_entities())

    total_updated = 0
    offset = 0
    while True:
        batch = get_articles_with_entities(offset=offset, batch_size=batch_size)
        if not batch:
            break

        for url, entities in batch:
            normalized = normalize_entities(entities)
            if normalized != entities:
                update_entities(url, normalized)
                total_updated += 1

        offset += batch_size
        logger.info(f"Entity backfill: processed {offset} articles, {total_updated} updated so far")

    logger.info(f"Entity normalization backfill complete — {total_updated} articles updated")


def _fetch_image(url: str) -> tuple[str, str]:
    """Fetch a single article URL and return (url, image_url_or_empty)."""
    if any(pat in url for pat in SKIP_URL_PATTERNS):
        return url, ""
    try:
        import trafilatura
        html = trafilatura.fetch_url(url)
        if html:
            data = _parse(html, url)
            if data and data.get("image"):
                return url, data["image"]
    except Exception as e:
        logger.warning(f"Image backfill failed for {url}: {e}")
    return url, ""


def run_image_backfill(workers: int = 6, batch_size: int = 200) -> None:
    """Fetch og:image for articles that don't have one yet."""
    logger.info("Image backfill started")
    total_processed = 0
    total_found = 0

    while True:
        urls = get_articles_without_images(batch_size)
        if not urls:
            break

        logger.info(f"Image backfill: {len(urls)} articles to check")

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_fetch_image, url): url for url in urls}
            for future in as_completed(futures):
                url, image_url = future.result()
                set_image_url(url, image_url)
                total_processed += 1
                if image_url:
                    total_found += 1

        logger.info(f"Image backfill progress: {total_processed} processed, {total_found} found")
