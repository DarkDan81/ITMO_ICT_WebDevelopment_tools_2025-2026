import re
from urllib.parse import urlparse

import requests
from sqlmodel import Session

from app.models import ParsedPage

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def extract_title(html: str) -> str:
    match = TITLE_RE.search(html)
    if not match:
        return "Title not found"
    title = re.sub(r"\s+", " ", match.group(1)).strip()
    return title or "Empty title"


def source_name_from_url(url: str) -> str:
    hostname = urlparse(url).hostname or "unknown"
    return hostname.removeprefix("www.")


def parse_url_and_save(url: str, session: Session) -> ParsedPage:
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    title = extract_title(response.text)
    page = ParsedPage(
        url=url,
        source_name=source_name_from_url(url),
        title=title,
        fetch_method="docker-http-parser",
        status_code=response.status_code,
    )
    session.add(page)
    session.commit()
    session.refresh(page)
    return page
