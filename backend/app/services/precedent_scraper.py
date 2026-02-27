"""Dynamic precedent scraping with cache-first retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
import re
from time import sleep
from typing import Optional
from urllib.parse import quote_plus, urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from pypdf import PdfReader
try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - optional fallback for constrained envs
    BeautifulSoup = None
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.scraped_case import ScrapedCase


@dataclass
class ScrapedPage:
    """Container for normalized scraped page content."""

    url: str
    title: str
    raw_text: str
    pdf_url: Optional[str] = None
    pdf_text: Optional[str] = None


_ROBOTS_CACHE: dict[str, RobotFileParser] = {}


def _build_session() -> requests.Session:
    settings = get_settings()
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": settings.PRECEDENT_SCRAPER_USER_AGENT,
            "Accept-Language": "en-IN,en;q=0.9",
        }
    )
    return session


def _sleep_with_rate_limit() -> None:
    settings = get_settings()
    if settings.PRECEDENT_SCRAPER_DELAY_SECONDS > 0:
        sleep(settings.PRECEDENT_SCRAPER_DELAY_SECONDS)


def _is_allowed_by_robots(url: str, session: requests.Session) -> bool:
    settings = get_settings()
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    parser = _ROBOTS_CACHE.get(robots_url)
    if parser is None:
        parser = RobotFileParser()
        try:
            _sleep_with_rate_limit()
            response = session.get(robots_url)
            if response.ok:
                parser.parse(response.text.splitlines())
            else:
                parser.parse([])
        except requests.RequestException:
            # If robots cannot be fetched due transient network errors,
            # continue with conservative rate-limited requests.
            return True
        _ROBOTS_CACHE[robots_url] = parser

    return parser.can_fetch(settings.PRECEDENT_SCRAPER_USER_AGENT, url)


def _fetch_html(url: str, session: requests.Session) -> str:
    _sleep_with_rate_limit()
    response = session.get(url)
    response.raise_for_status()
    return response.text


def search_case_links(query: str) -> list[str]:
    """Search legal precedent links for a query using IndianKanoon."""
    settings = get_settings()
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return []

    session = _build_session()
    search_url = (
        f"{settings.PRECEDENT_SCRAPER_BASE_URL}?formInput={quote_plus(cleaned_query)}"
    )
    if not _is_allowed_by_robots(search_url, session):
        return []

    html = _fetch_html(search_url, session)
    links: list[str] = []
    seen: set[str] = set()

    if BeautifulSoup is not None:
        soup = BeautifulSoup(html, "html.parser")
        hrefs = [anchor.get("href", "").strip() for anchor in soup.select("a[href]")]
    else:
        hrefs = re.findall(r"""href=["']([^"']+)["']""", html, flags=re.I)

    for href in hrefs:
        if not href or "/doc/" not in href:
            continue
        absolute_url = urljoin("https://indiankanoon.org", href)
        normalized = absolute_url.split("?")[0]
        if normalized in seen:
            continue
        seen.add(normalized)
        links.append(normalized)
        if len(links) >= settings.PRECEDENT_SCRAPER_MAX_RESULTS:
            break

    return links


def _clean_text(value: str) -> str:
    return " ".join((value or "").split())


def _strip_html_tags(raw_html: str) -> str:
    cleaned = re.sub(r"<(script|style|noscript).*?>.*?</\1>", " ", raw_html, flags=re.I | re.S)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    return _clean_text(cleaned)


def _extract_pdf_url_from_html(html: str, page_url: str) -> Optional[str]:
    """Best-effort extraction of a PDF URL from a legal precedent page."""
    if not html:
        return None

    candidates: list[str] = []
    if BeautifulSoup is not None:
        soup = BeautifulSoup(html, "html.parser")
        for anchor in soup.select("a[href]"):
            href = (anchor.get("href") or "").strip()
            if not href or href.lower().startswith("javascript:") or href.startswith("#"):
                continue
            label = " ".join(
                [
                    anchor.get_text(" ", strip=True),
                    anchor.get("title", ""),
                    anchor.get("aria-label", ""),
                ]
            ).lower()
            href_lower = href.lower()
            if ".pdf" in href_lower or "type=pdf" in href_lower or "pdf" in label:
                candidates.append(urljoin(page_url, href))
    else:
        for href in re.findall(r"""href=["']([^"']+)["']""", html, flags=re.I):
            if href.lower().startswith("javascript:") or href.startswith("#"):
                continue
            href_lower = href.lower()
            if ".pdf" in href_lower or "type=pdf" in href_lower:
                candidates.append(urljoin(page_url, href))

    # Common IndianKanoon fallback for doc pages.
    if "/doc/" in page_url:
        candidates.append(f"{page_url.rstrip('/')}/?type=pdf")

    seen: set[str] = set()
    for candidate in candidates:
        normalized = candidate.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        if normalized.lower().startswith(("http://", "https://")):
            return normalized
    return None


def _extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes; returns empty string on parse failure."""
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        pages: list[str] = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                pages.append(page_text)
        return _clean_text(" ".join(pages))
    except Exception:
        return ""


def _fetch_pdf_text(pdf_url: str, session: requests.Session) -> str:
    """Fetch and parse PDF text from a URL."""
    _sleep_with_rate_limit()
    response = session.get(pdf_url)
    response.raise_for_status()
    return _extract_text_from_pdf_bytes(response.content)


def scrape_case(url: str) -> ScrapedPage:
    """Scrape a precedent URL and extract title + raw text content."""
    settings = get_settings()
    session = _build_session()
    if not _is_allowed_by_robots(url, session):
        raise ValueError(f"Scraping blocked by robots.txt for URL: {url}")

    html = _fetch_html(url, session)
    if BeautifulSoup is not None:
        soup = BeautifulSoup(html, "html.parser")

        for selector in ("script", "style", "noscript", "header", "footer", "nav", "form"):
            for tag in soup.select(selector):
                tag.extract()

        title = _clean_text(soup.title.get_text(" ", strip=True) if soup.title else "")
        primary_container = (
            soup.select_one("#judgments")
            or soup.select_one(".judgments")
            or soup.select_one("article")
            or soup.body
            or soup
        )
        raw_text = _clean_text(primary_container.get_text(" ", strip=True))
    else:
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.I | re.S)
        title = _clean_text(title_match.group(1) if title_match else "")
        raw_text = _strip_html_tags(html)

    pdf_url = _extract_pdf_url_from_html(html=html, page_url=url)
    pdf_text = ""
    if pdf_url:
        try:
            if _is_allowed_by_robots(pdf_url, session):
                pdf_text = _fetch_pdf_text(pdf_url=pdf_url, session=session)
        except Exception:
            pdf_text = ""

    if pdf_text:
        # Prefer court-copy PDF text when available; preserve some page context.
        raw_text = _clean_text(f"{pdf_text} {raw_text}")

    if not title:
        title = "Untitled Precedent"

    if len(raw_text) > settings.PRECEDENT_SCRAPER_MAX_TEXT_CHARS:
        raw_text = raw_text[: settings.PRECEDENT_SCRAPER_MAX_TEXT_CHARS]

    if not raw_text:
        raise ValueError(f"No readable text found for URL: {url}")

    return ScrapedPage(
        url=url,
        title=title,
        raw_text=raw_text,
        pdf_url=pdf_url,
        pdf_text=pdf_text or None,
    )


def _get_cached_case(db: Session, url: str) -> Optional[ScrapedCase]:
    return db.query(ScrapedCase).filter(ScrapedCase.url == url).first()


def get_or_scrape(url: str, db: Session) -> ScrapedCase:
    """Return cached scraped case or scrape + store it on first use."""
    cached = _get_cached_case(db, url)
    if cached is not None and (cached.raw_text or "").strip():
        return cached

    page = scrape_case(url)
    if cached is None:
        cached = ScrapedCase(
            url=page.url,
            title=page.title,
            raw_text=page.raw_text,
            embeddings=None,
            scraped_at=datetime.utcnow(),
        )
        db.add(cached)
    else:
        cached.title = page.title
        cached.raw_text = page.raw_text
        cached.scraped_at = datetime.utcnow()

    db.commit()
    db.refresh(cached)
    return cached
