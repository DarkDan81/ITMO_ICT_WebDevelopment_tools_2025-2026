"""Общие действия парсеров. Ошибка одного сайта не прерывает остальные."""
from html.parser import HTMLParser
from time import perf_counter

import requests
from charset_normalizer import from_bytes

from app.config import REQUEST_TIMEOUT
from app.db import engine, init_db
from app.parse_shared import save_page_result


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


def extract_title(content: bytes) -> str:
    decoded = from_bytes(content).best()
    parser = TitleParser()
    parser.feed(str(decoded) if decoded is not None else content.decode("utf-8", errors="replace"))
    title = " ".join("".join(parser.parts).split())
    if not title:
        raise ValueError("У страницы нет заголовка title")
    return title[:500]


def fetch_and_save(url: str, method: str) -> bool:
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        title = extract_title(response.content)
        save_page_result(url, title, response.status_code, method)
        print(f"[{method}] {response.status_code} | {url} | {title}", flush=True)
        return True
    except Exception as error:
        # Учебный пакетный запуск: показываем сбой, затем продолжаем список.
        print(f"[{method}] ERROR | {url} | {type(error).__name__}: {error}", flush=True)
        return False


def prepare() -> None:
    init_db()
    engine.dispose()  # Соединения родителя не должны попасть в дочерние процессы.


def run_and_print(method: str, count: int, runner) -> None:
    prepare()
    started = perf_counter()
    successful = runner()
    print(f"Approach: {method}")
    print(f"Successful: {successful}; Failed: {count - successful}; Total: {count}")
    print(f"Duration: {perf_counter() - started:.6f} seconds")
