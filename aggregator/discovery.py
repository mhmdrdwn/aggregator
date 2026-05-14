import logging
import re
from urllib.parse import quote_plus
import feedparser

from .config import NORWEGIAN_RSS_FEEDS

logger = logging.getLogger(__name__)


def _is_google_news(url: str) -> bool:
    return "news.google.com" in url


def _clean_google_title(title: str, source_name: str) -> str:
    """Remove ' - SourceName' suffix that Google News appends to titles."""
    suffix = f" - {source_name}"
    if title.endswith(suffix):
        return title[: -len(suffix)]
    # Also strip a trailing ' - <anything>' as fallback
    cleaned = re.sub(r"\s+-\s+[^-]+$", "", title)
    return cleaned if cleaned else title


def get_urls_from_rss(feed_url: str) -> list[dict]:
    feed = feedparser.parse(feed_url)
    feed_title = feed.feed.get("title", feed_url)
    is_google = _is_google_news(feed_url)

    results = []
    for entry in feed.entries:
        link = getattr(entry, "link", None)
        if not link:
            continue

        title = getattr(entry, "title", "")
        source = feed_title

        if is_google:
            entry_source = getattr(getattr(entry, "source", None), "title", None)
            if entry_source:
                source = entry_source
                title = _clean_google_title(title, entry_source)
            # CBMi URL = stable dedup key; link_url = Google News search users can actually open
            search_url = f"https://news.google.com/search?q={quote_plus(title)}&hl=no&gl=NO&ceid=NO:no"
            results.append(
                {
                    "url": link,
                    "title": title,
                    "published": entry.get("published", ""),
                    "source": source,
                    "link_url": search_url,
                    "title_only": True,
                }
            )
        else:
            results.append(
                {
                    "url": link,
                    "title": title,
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
