import logging
import time
import urllib.request
import feedparser

from .config import NORWEGIAN_RSS_FEEDS

logger = logging.getLogger(__name__)


def _resolve_google_url(url: str) -> str:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.url
    except Exception:
        return url


def _is_google_news(url: str) -> bool:
    return "news.google.com" in url


def get_urls_from_rss(feed_url: str) -> list[dict]:
    feed = feedparser.parse(feed_url)
    source = feed.feed.get("title", feed_url)
    is_google = _is_google_news(feed_url)

    results = []
    for entry in feed.entries:
        link = getattr(entry, "link", None)
        if not link:
            continue

        if is_google:
            link = _resolve_google_url(link)
            entry_source = getattr(getattr(entry, "source", None), "title", None)
            source = entry_source or source
            time.sleep(0.3)  # avoid hammering Google's redirect service

        results.append(
            {
                "url": link,
                "title": getattr(entry, "title", ""),
                "published": entry.get("published", ""),
                "source": source,
            }
        )

    return results


def discover_all() -> list[dict]:
    all_urls: list[dict] = []

    for feed_url in NORWEGIAN_RSS_FEEDS:
        try:
            items = get_urls_from_rss(feed_url)
            logger.info(f"RSS {feed_url}: {len(items)} items")
            all_urls.extend(items)
        except Exception as e:
            logger.error(f"RSS failed for {feed_url}: {e}")

    seen: set[str] = set()
    unique: list[dict] = []
    for item in all_urls:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique.append(item)

    logger.info(f"Discovered {len(unique)} unique URLs")
    return unique
