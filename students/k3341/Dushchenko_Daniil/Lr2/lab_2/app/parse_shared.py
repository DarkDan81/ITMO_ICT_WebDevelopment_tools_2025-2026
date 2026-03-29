from __future__ import annotations

import re
from dataclasses import dataclass
from time import perf_counter
from urllib.parse import urlparse

from sqlmodel import Session, delete

from app.db import get_session, init_db
from app.models import ParsedPage

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


@dataclass
class ParseResult:
    approach: str
    processed: int
    duration: float


def extract_title(html: str) -> str:
    match = TITLE_RE.search(html)
    if not match:
        return "Title not found"
    title = re.sub(r"\s+", " ", match.group(1)).strip()
    return title or "Empty title"


def source_name_from_url(url: str) -> str:
    hostname = urlparse(url).hostname or "unknown"
    return hostname.removeprefix("www.")


def reset_results(fetch_method: str) -> None:
    init_db()
    with get_session() as session:
        session.exec(delete(ParsedPage).where(ParsedPage.fetch_method == fetch_method))
        session.commit()


def save_page_result(
    url: str,
    title: str,
    status_code: int,
    fetch_method: str,
    session: Session | None = None,
) -> None:
    owns_session = session is None
    if session is None:
        session = get_session()

    page = ParsedPage(
        url=url,
        source_name=source_name_from_url(url),
        title=title,
        fetch_method=fetch_method,
        status_code=status_code,
    )
    session.add(page)
    session.commit()

    if owns_session:
        session.close()


def print_page_result(url: str, title: str, status_code: int, fetch_method: str) -> None:
    print(f"[{fetch_method}] {status_code} | {url} | {title}")


def timed_parse_run(approach: str, runner) -> ParseResult:
    started = perf_counter()
    processed = runner()
    duration = perf_counter() - started
    return ParseResult(
        approach=approach,
        processed=processed,
        duration=duration,
    )


def print_parse_result(result: ParseResult) -> None:
    print(f"Approach: {result.approach}")
    print(f"Processed pages: {result.processed}")
    print(f"Duration: {result.duration:.6f} seconds")
