import ipaddress
import socket
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin

import requests
from charset_normalizer import from_bytes
from sqlmodel import Session
from app.models import ParsedPage


class TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside = False
        self.done = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "title" and not self.done:
            self.inside = True

    def handle_endtag(self, tag):
        if tag == "title" and self.inside:
            self.inside = False
            self.done = True

    def handle_data(self, data):
        if self.inside:
            self.parts.append(data)


def validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Нужен публичный HTTP/HTTPS URL без логина и пароля")
    if parsed.port not in {None, 80, 443}:
        raise ValueError("Разрешены порты 80 и 443")
    addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443)
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError("Внутренние адреса не поддерживаются")


def parse_url_and_save(url: str, session: Session) -> ParsedPage:
    current = url
    for _ in range(6):
        validate_public_url(current)
        with requests.get(current, timeout=(3, 12), allow_redirects=False, stream=True) as response:
            if response.is_redirect:
                current = urljoin(current, response.headers["Location"])
                continue
            response.raise_for_status()
            content = bytearray()
            for chunk in response.iter_content(65536):
                content.extend(chunk)
                if len(content) > 2_000_000:
                    raise ValueError("Страница больше 2 МБ")
            decoded = from_bytes(bytes(content)).best()
            parser = TitleParser()
            parser.feed(str(decoded) if decoded is not None else content.decode("utf-8", errors="replace"))
            title = " ".join("".join(parser.parts).split())
            if not title:
                raise ValueError("На странице нет title")
            page = ParsedPage(url=url, source_name=(urlparse(url).hostname or "unknown")[:100],
                              title=title[:500], fetch_method="docker-http-parser", status_code=response.status_code)
            session.add(page)
            session.commit()
            session.refresh(page)
            return page
    raise ValueError("Слишком много перенаправлений")
