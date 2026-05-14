import json
import logging
from urllib.parse import urlparse

import trafilatura

from .config import PLAYWRIGHT_DOMAINS, SKIP_URL_PATTERNS

logger = logging.getLogger(__name__)

_EXTRACT_OPTS = dict(
    output_format="json",
    with_metadata=True,
    include_comments=False,
    favor_precision=True,
)


def _hostname(url: str) -> str:
    try:
        return urlparse(url).hostname.removeprefix("www.")
    except Exception:
        return ""


def _parse(html: str | None, url: str = "") -> dict | None:
    if not html:
        return None
    raw = trafilatura.extract(html, url=url or None, **_EXTRACT_OPTS)
    if raw:
        data = json.loads(raw)
        if url and not data.get("url"):
            data["url"] = url
        return data
    return None


def fetch_article_trafilatura(url: str) -> dict | None:
    try:
        html = trafilatura.fetch_url(url)
        return _parse(html, url)
    except Exception as e:
        logger.warning(f"Trafilatura failed for {url}: {e}")
        return None


def fetch_article_stealth(url: str) -> dict | None:
    try:
        from scrapling.fetchers import StealthyFetcher
        page = StealthyFetcher.fetch(url)
        return _parse(page.html_content, url)
    except Exception as e:
        logger.warning(f"StealthyFetcher failed for {url}: {e}")
        return None


def fetch_article_playwright(url: str) -> dict | None:
    try:
        from scrapling.fetchers import DynamicFetcher
        page = DynamicFetcher.fetch(url, headless=True)
        return _parse(page.html_content, url)
    except Exception as e:
        logger.warning(f"DynamicFetcher failed for {url}: {e}")
        return None


def fetch_article(url: str) -> dict | None:
    # Skip video pages and other known non-article URLs
    if any(pat in url for pat in SKIP_URL_PATTERNS):
        logger.debug(f"Skipping non-article URL: {url}")
        return None

    # Known JS-rendered sites — go straight to Playwright
    if _hostname(url) in PLAYWRIGHT_DOMAINS:
        logger.debug(f"Using Playwright directly for {url}")
        return fetch_article_playwright(url)

    # Fast path: plain HTTP
    article = fetch_article_trafilatura(url)
    if article and article.get("text"):
        return article

    # Fallback 1: stealth curl_cffi (handles Cloudflare bot checks)
    logger.info(f"Falling back to StealthyFetcher for {url}")
    article = fetch_article_stealth(url)
    if article and article.get("text"):
        return article

    # Fallback 2: full headless browser (JS-rendered content)
    logger.info(f"Falling back to DynamicFetcher for {url}")
    return fetch_article_playwright(url)
