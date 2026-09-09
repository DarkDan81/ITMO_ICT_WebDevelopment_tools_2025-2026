from urllib.parse import urlparse
from app.db import get_session
from app.models import ParsedPage


def save_page_result(url: str, title: str, status_code: int, fetch_method: str) -> None:
    with get_session() as session:
        session.add(ParsedPage(url=url, title=title,
                               source_name=(urlparse(url).hostname or "unknown")[:100],
                               status_code=status_code, fetch_method=fetch_method))
        session.commit()
