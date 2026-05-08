import hashlib
import logging
import os
import re
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger("news_scraper")
logging.basicConfig(level=logging.INFO)

USER_AGENT = os.getenv(
    "SCRAPER_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
)
REQUEST_TIMEOUT = int(os.getenv("SCRAPER_TIMEOUT_SECONDS", "30"))
REQUEST_DELAY = float(os.getenv("SCRAPER_DELAY_SECONDS", "1.0"))
NEWS_SOURCES = [s.strip().lower() for s in os.getenv("NEWS_SOURCES", "bbc,hespress").split(",") if s.strip()]
MAX_ARTICLES_PER_SOURCE = int(os.getenv("SCRAPER_MAX_ARTICLES_PER_SOURCE", "6"))

BBC_HOME = "https://www.bbc.com/news"
HESPRESS_HOME = "https://www.hespress.com"
FRANCE24_HOME = "https://www.france24.com/fr/"
FRANCE24_RSS = "https://www.france24.com/fr/rss"


def requests_session_with_retries(total_retries: int = 3, backoff_factor: float = 0.5) -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods={"GET"},
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9,fr;q=0.8,ar;q=0.7"})
    return session


def normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def article_id_from_url(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


def parse_datetime(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    cleaned = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(cleaned)
    except ValueError:
        try:
            dt = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def get_html(session: requests.Session, url: str) -> str:
    logger.info("Fetching %s", url)
    response = session.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def unique_urls(urls: Iterable[str]) -> List[str]:
    seen = set()
    ordered = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            ordered.append(url)
    return ordered


def is_bbc_article(url: str) -> bool:
    parsed = urlparse(url)
    if "bbc.com" not in parsed.netloc or not parsed.path.startswith("/news"):
        return False
    forbidden = ("/news/live", "/news/topics", "/news/av", "/newsround", "/news/world/service")
    return not any(fragment in parsed.path for fragment in forbidden)


def is_hespress_article(url: str) -> bool:
    parsed = urlparse(url)
    if "hespress.com" not in parsed.netloc:
        return False
    forbidden = ("/category/", "/author/", "/tag/", "/page/", "/wp-content/", "/feed/")
    if any(fragment in parsed.path for fragment in forbidden):
        return False
    return len(parsed.path.strip("/")) > 0


def is_france24_article(url: str) -> bool:
    parsed = urlparse(url)
    if "france24.com" not in parsed.netloc:
        return False
    forbidden = ("/live/", "/video/", "/rss", "/programme/", "/sports/", "/search/")
    if any(fragment in parsed.path for fragment in forbidden):
        return False
    return parsed.path.startswith("/fr/") or parsed.path.startswith("/en/")


def discover_article_urls(session: requests.Session, home_url: str, source: str, limit: int) -> List[str]:
    html = get_html(session, home_url)
    soup = BeautifulSoup(html, "html.parser")
    urls: List[str] = []
    for anchor in soup.select("a[href]"):
        href = anchor.get("href")
        if not href:
            continue
        full_url = urljoin(home_url, href)
        if source == "bbc" and is_bbc_article(full_url):
            urls.append(full_url)
        elif source == "hespress" and is_hespress_article(full_url):
            urls.append(full_url)
        elif source == "france24" and is_france24_article(full_url):
            urls.append(full_url)
    urls = unique_urls(urls)
    logger.info("Discovered %d candidate URLs on %s", len(urls), source)
    return urls[: max(limit * 3, limit)]


def extract_meta(soup: BeautifulSoup, names: List[str], attr: str = "content") -> Optional[str]:
    for name in names:
        tag = soup.find("meta", attrs={"name": name}) or soup.find("meta", attrs={"property": name})
        if tag and tag.get(attr):
            return normalize_text(tag.get(attr))
    return None


def extract_rss_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return normalize_text(BeautifulSoup(value, "html.parser").get_text(" ", strip=True))


def fetch_rss_items(session: requests.Session, feed_url: str) -> List[Dict[str, str]]:
    xml_text = get_html(session, feed_url)
    root = ElementTree.fromstring(xml_text)
    items: List[Dict[str, str]] = []
    for item in root.findall(".//item"):
        title = item.findtext("title") or ""
        link = item.findtext("link") or ""
        pub_date = item.findtext("pubDate") or ""
        category = item.findtext("category") or ""
        description = item.findtext("description") or ""
        items.append(
            {
                "title": title.strip(),
                "link": link.strip(),
                "pub_date": pub_date.strip(),
                "category": category.strip(),
                "description": description.strip(),
            }
        )
    return items


def extract_article_text(soup: BeautifulSoup) -> str:
    selectors = [
        "article p",
        "main p",
        "div[data-component='text-block'] p",
        "div.entry-content p",
        "div.article-body p",
        "div.story-body__inner p",
    ]
    paragraphs: List[str] = []
    for selector in selectors:
        candidate = [normalize_text(node.get_text(" ", strip=True)) for node in soup.select(selector)]
        candidate = [item for item in candidate if len(item) > 30]
        if candidate:
            paragraphs = candidate
            break
    if not paragraphs:
        paragraphs = [
            normalize_text(node.get_text(" ", strip=True))
            for node in soup.select("p")
            if len(normalize_text(node.get_text(" ", strip=True))) > 30
        ]
    cleaned: List[str] = []
    for paragraph in paragraphs:
        if paragraph not in cleaned:
            cleaned.append(paragraph)
    return "\n\n".join(cleaned)


def extract_article_common(url: str, source: str, html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    title = extract_meta(soup, ["og:title", "twitter:title", "headline"])
    if not title and soup.find("h1"):
        title = normalize_text(soup.find("h1").get_text(" ", strip=True))

    author = extract_meta(soup, ["author", "article:author", "parsely-author"])
    if not author:
        byline = soup.select_one("[data-testid='byline-name']") or soup.select_one("[rel='author']") or soup.select_one(".byline__name")
        if byline:
            author = normalize_text(byline.get_text(" ", strip=True))

    published_at = extract_meta(soup, ["article:published_time", "date", "pubdate", "publish-date"])
    if not published_at:
        time_tag = soup.find("time")
        if time_tag and time_tag.get("datetime"):
            published_at = normalize_text(time_tag.get("datetime"))
    published_at = parse_datetime(published_at)

    category = extract_meta(soup, ["article:section", "section", "category"])
    if not category:
        breadcrumb = soup.select_one("nav[aria-label*='Breadcrumb'] a") or soup.select_one(".breadcrumb a")
        if breadcrumb:
            category = normalize_text(breadcrumb.get_text(" ", strip=True))
    if not category:
        category = source.title()

    content = extract_article_text(soup)
    fetched_at = datetime.now(timezone.utc).isoformat()

    source_home = {
        "bbc": BBC_HOME,
        "hespress": HESPRESS_HOME,
        "france24": FRANCE24_HOME,
    }.get(source, "")

    return {
        "article_id": article_id_from_url(url),
        "source": source,
        "source_name": source.title(),
        "source_home": source_home,
        "title": title or "",
        "author": author or "",
        "published_at": published_at,
        "category": category or "",
        "content": content,
        "url": url,
        "fetched_at": fetched_at,
        "language": soup.html.get("lang") if soup.html else None,
        "raw_html_url": url,
    }


def scrape_bbc(session: requests.Session, limit: int) -> List[Dict[str, Any]]:
    articles: List[Dict[str, Any]] = []
    for url in discover_article_urls(session, BBC_HOME, "bbc", limit):
        try:
            article = extract_article_common(url, "bbc", get_html(session, url))
            if article.get("title") and article.get("content"):
                articles.append(article)
        except Exception as exc:
            logger.warning("Failed to parse BBC article %s: %s", url, exc)
        time.sleep(REQUEST_DELAY)
        if len(articles) >= limit:
            break
    return articles


def scrape_hespress(session: requests.Session, limit: int) -> List[Dict[str, Any]]:
    articles: List[Dict[str, Any]] = []
    for url in discover_article_urls(session, HESPRESS_HOME, "hespress", limit):
        try:
            article = extract_article_common(url, "hespress", get_html(session, url))
            if article.get("title") and article.get("content"):
                articles.append(article)
        except Exception as exc:
            logger.warning("Failed to parse Hespress article %s: %s", url, exc)
        time.sleep(REQUEST_DELAY)
        if len(articles) >= limit:
            break
    return articles


def scrape_france24(session: requests.Session, limit: int) -> List[Dict[str, Any]]:
    articles: List[Dict[str, Any]] = []
    try:
        rss_items = fetch_rss_items(session, FRANCE24_RSS)
    except Exception as exc:
        logger.warning("Failed to fetch France 24 RSS feed: %s", exc)
        return articles
    for item in rss_items:
        if len(articles) >= limit:
            break
        url = item.get("link") or ""
        if not url:
            continue
        content = extract_rss_text(item.get("description"))
        article = {
            "article_id": article_id_from_url(url),
            "source": "france24",
            "source_name": "France24",
            "source_home": FRANCE24_HOME,
            "title": normalize_text(item.get("title")),
            "author": "",
            "published_at": parse_datetime(item.get("pub_date")),
            "category": normalize_text(item.get("category")) or "France24",
            "content": content,
            "url": url,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "language": "fr",
            "raw_html_url": url,
        }
        if article.get("title") and article.get("content"):
            articles.append(article)
        time.sleep(REQUEST_DELAY)
    return articles


def scrape_news_articles(limit_per_source: Optional[int] = None, sources: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    session = requests_session_with_retries()
    active_sources = sources or NEWS_SOURCES
    limit = limit_per_source or MAX_ARTICLES_PER_SOURCE
    articles: List[Dict[str, Any]] = []

    for source in active_sources:
        if source == "bbc":
            articles.extend(scrape_bbc(session, limit))
        elif source == "hespress":
            articles.extend(scrape_hespress(session, limit))
        elif source == "france24":
            articles.extend(scrape_france24(session, limit))
        else:
            logger.info("Skipping unsupported source %s", source)

    logger.info("Scraped %d articles total", len(articles))
    return articles


if __name__ == "__main__":
    data = scrape_news_articles()
    print({"articles_count": len(data)})
