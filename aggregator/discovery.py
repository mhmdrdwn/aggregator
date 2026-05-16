import logging
import re
from datetime import datetime, timezone, timedelta
import feedparser
import requests

from .config import NORWEGIAN_RSS_FEEDS, NORWEGIAN_NEWS_SITEMAPS, AMEDIA_PAPERS

logger = logging.getLogger(__name__)

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"})

_SITEMAP_MAX_AGE_HOURS = 48

# Amedia article URL pattern: /{slug}/{type}/{prefix}-{pub_id}-{article_id}
# Most papers use prefix 5; some older Amedia papers (e.g. Østlendingen) use 80.
# Types: s=story, f=feature, o=opinion (skip v=video, g=gallery)
_AMEDIA_ARTICLE_RE = re.compile(r'/[^/"\s<>]+/[sfo]/\d+-\d+-\d+')


def _parse_sitemap_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%dT%H:%M%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def get_urls_from_sitemap(sitemap_url: str, source_name: str) -> list[dict]:
    try:
        resp = _SESSION.get(sitemap_url, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.error("Sitemap fetch failed for %s: %s", sitemap_url, e)
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=_SITEMAP_MAX_AGE_HOURS)
    results = []

    for entry in re.finditer(r"<url>(.*?)</url>", resp.text, re.S):
        block = entry.group(1)

        loc = re.search(r"<loc>(https?://[^<]+)</loc>", block)
        if not loc:
            continue
        url = loc.group(1).strip()

        lastmod = re.search(r"<lastmod>([^<]+)</lastmod>", block)
        published = ""
        if lastmod:
            dt = _parse_sitemap_date(lastmod.group(1))
            if dt:
                if dt < cutoff:
                    continue
                published = dt.isoformat()

        title_tag = re.search(r"<news:title>([^<]+)</news:title>", block)
        title = title_tag.group(1).strip() if title_tag else ""

        results.append({"url": url, "title": title, "published": published, "source": source_name})

    logger.info("Sitemap %s: %d recent items", sitemap_url, len(results))
    return results


def get_urls_from_homepage(base_url: str, source_name: str) -> list[dict]:
    """Crawl an Amedia paper homepage and extract article links."""
    try:
        resp = _SESSION.get(base_url, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.error("Homepage fetch failed for %s: %s", base_url, e)
        return []

    seen: set[str] = set()
    results = []

    for match in _AMEDIA_ARTICLE_RE.finditer(resp.text):
        path = match.group(0)
        url = base_url.rstrip("/") + path
        if url in seen:
            continue
        seen.add(url)
        results.append({"url": url, "title": "", "published": "", "source": source_name})

    logger.info("Homepage %s: %d articles", base_url, len(results))
    return results


def get_urls_from_rss(feed_url: str) -> list[dict]:
    feed = feedparser.parse(feed_url)
    feed_title = feed.feed.get("title", feed_url)
    results = []
    for entry in feed.entries:
        link = getattr(entry, "link", None)
        if not link:
            continue
        results.append({
            "url": link,
            "title": getattr(entry, "title", ""),
            "published": entry.get("published", ""),
            "source": feed_title,
        })
    return results


def discover_all() -> list[dict]:
    all_items: list[dict] = []

    for feed_url in NORWEGIAN_RSS_FEEDS:
        try:
            items = get_urls_from_rss(feed_url)
            logger.info("RSS %s: %d items", feed_url, len(items))
            all_items.extend(items)
        except Exception as e:
            logger.error("RSS failed for %s: %s", feed_url, e)

    for sitemap_url, source_name in NORWEGIAN_NEWS_SITEMAPS:
        try:
            items = get_urls_from_sitemap(sitemap_url, source_name)
            all_items.extend(items)
        except Exception as e:
            logger.error("Sitemap failed for %s: %s", sitemap_url, e)

    for homepage_url, source_name in AMEDIA_PAPERS:
        try:
            items = get_urls_from_homepage(homepage_url, source_name)
            all_items.extend(items)
        except Exception as e:
            logger.error("Homepage crawl failed for %s: %s", homepage_url, e)

    seen_urls: set[str] = set()
    unique: list[dict] = []
    for item in all_items:
        if item["url"] not in seen_urls:
            seen_urls.add(item["url"])
            unique.append(item)

    logger.info("Discovered %d unique URLs", len(unique))
    return unique
