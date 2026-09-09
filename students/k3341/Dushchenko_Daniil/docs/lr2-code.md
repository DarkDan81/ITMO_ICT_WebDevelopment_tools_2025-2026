# Исходный код LR2

Код соответствует текущим файлам проекта.

## Lr2/lab_2/app/compute_shared.py

```python
from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter


@dataclass
class ComputeResult:
    approach: str
    workers: int
    total: int
    duration: float


def calculate_sum(start: int, end: int, mode: str = "formula") -> int:
    """Формула для 10^13; цикл — для сравнения CPU-bound работы."""
    if mode == "loop":
        total = 0
        for number in range(start, end + 1):
            total += number
        return total
    count = end - start + 1
    return (start + end) * count // 2


def split_range(limit: int, chunks: int) -> list[tuple[int, int]]:
    chunks = min(limit, chunks)
    chunk_size = limit // chunks
    ranges: list[tuple[int, int]] = []
    start = 1

    for index in range(chunks):
        end = start + chunk_size - 1
        if index == chunks - 1:
            end = limit
        ranges.append((start, end))
        start = end + 1

    return ranges


def timed_run(approach: str, workers: int, runner) -> ComputeResult:
    started = perf_counter()
    total = runner()
    duration = perf_counter() - started
    return ComputeResult(
        approach=approach,
        workers=workers,
        total=total,
        duration=duration,
    )


def print_compute_result(result: ComputeResult) -> None:
    print(f"Approach: {result.approach}")
    print(f"Workers: {result.workers}")
    print(f"Total sum: {result.total}")
    print(f"Duration: {result.duration:.6f} seconds")
```

## Lr2/lab_2/app/config.py

```python
import os
import json

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres@localhost:5432/personal_finance_practice_3_db",
)

SUM_LIMIT = int(os.getenv("LAB2_SUM_LIMIT", "10000000000000"))
SUM_MODE = os.getenv("LAB2_SUM_MODE", "formula")
DEFAULT_WORKERS = int(os.getenv("LAB2_WORKERS", "4"))
if SUM_LIMIT < 1 or DEFAULT_WORKERS < 1 or SUM_MODE not in {"formula", "loop"}:
    raise ValueError("Проверьте LAB2_SUM_LIMIT, LAB2_WORKERS и LAB2_SUM_MODE")
REQUEST_TIMEOUT = 12

URLS = json.loads(os.getenv("LAB2_URLS", '["https://www.worldbank.org/", "https://www.federalreserve.gov/", "https://www.cbr.ru/", "https://www.bis.org/"]'))
if not URLS:
    raise ValueError("Список LAB2_URLS не должен быть пустым")


def split_items(items: list, workers: int) -> list[list]:
    """Размеры частей отличаются максимум на один элемент."""
    workers = min(workers, len(items))
    size, extra = divmod(len(items), workers)
    result = []
    start = 0
    for index in range(workers):
        end = start + size + (index < extra)
        result.append(items[start:end])
        start = end
    return result
```

## Lr2/lab_2/app/db.py

```python
from sqlmodel import Session, SQLModel, create_engine

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
```

## Lr2/lab_2/app/models.py

```python
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class ParsedPage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    url: str = Field(index=True, max_length=500)
    source_name: str = Field(max_length=100)
    title: str = Field(max_length=500)
    fetch_method: str = Field(max_length=30, index=True)
    status_code: int
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
```

## Lr2/lab_2/app/parse_shared.py

```python
from urllib.parse import urlparse
from app.db import get_session
from app.models import ParsedPage


def save_page_result(url: str, title: str, status_code: int, fetch_method: str) -> None:
    with get_session() as session:
        session.add(ParsedPage(url=url, title=title,
                               source_name=(urlparse(url).hostname or "unknown")[:100],
                               status_code=status_code, fetch_method=fetch_method))
        session.commit()
```

## Lr2/lab_2/app/parsing.py

```python
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
```

## Lr2/lab_2/task1_async.py

```python
import asyncio

from app.compute_shared import calculate_sum as sum_chunk, print_compute_result, split_range, timed_run
from app.config import DEFAULT_WORKERS, SUM_LIMIT, SUM_MODE


async def calculate_sum(start: int, end: int) -> int:
    if SUM_MODE == "formula":
        await asyncio.sleep(0)
        return sum_chunk(start, end)
    total = 0
    for offset, number in enumerate(range(start, end + 1), 1):
        total += number
        if offset % 100000 == 0:
            await asyncio.sleep(0)
    return total


def main() -> None:
    workers = DEFAULT_WORKERS
    ranges = split_range(SUM_LIMIT, workers)

    def runner() -> int:
        async def run_async() -> int:
            tasks = [calculate_sum(start, end) for start, end in ranges]
            return sum(await asyncio.gather(*tasks))

        return asyncio.run(run_async())

    result = timed_run("asyncio", workers, runner)
    assert result.total == SUM_LIMIT * (SUM_LIMIT + 1) // 2
    print(f"Mode: {SUM_MODE}; N: {SUM_LIMIT}")
    print_compute_result(result)


if __name__ == "__main__":
    main()
```

## Lr2/lab_2/task1_multiprocessing.py

```python
from multiprocessing import Pool, cpu_count

from app.compute_shared import calculate_sum as sum_chunk, print_compute_result, split_range, timed_run
from app.config import DEFAULT_WORKERS, SUM_LIMIT, SUM_MODE


def calculate_sum(start: int, end: int) -> int:
    return sum_chunk(start, end, SUM_MODE)


def _calculate_chunk(bounds: tuple[int, int]) -> int:
    return calculate_sum(*bounds)


def main() -> None:
    workers = min(DEFAULT_WORKERS, cpu_count())
    ranges = split_range(SUM_LIMIT, workers)

    def runner() -> int:
        with Pool(processes=workers) as pool:
            return sum(pool.map(_calculate_chunk, ranges))

    result = timed_run("multiprocessing", workers, runner)
    assert result.total == SUM_LIMIT * (SUM_LIMIT + 1) // 2
    print(f"Mode: {SUM_MODE}; N: {SUM_LIMIT}")
    print_compute_result(result)


if __name__ == "__main__":
    main()
```

## Lr2/lab_2/task1_threading.py

```python
import threading

from app.compute_shared import calculate_sum as sum_chunk, print_compute_result, split_range, timed_run
from app.config import DEFAULT_WORKERS, SUM_LIMIT, SUM_MODE


def calculate_sum(start: int, end: int) -> int:
    return sum_chunk(start, end, SUM_MODE)


def main() -> None:
    workers = DEFAULT_WORKERS
    ranges = split_range(SUM_LIMIT, workers)
    results = [0] * len(ranges)

    def worker(index: int, bounds: tuple[int, int]) -> None:
        results[index] = calculate_sum(*bounds)

    def runner() -> int:
        threads = [threading.Thread(target=worker, args=(i, bounds)) for i, bounds in enumerate(ranges)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        return sum(results)

    result = timed_run("threading", workers, runner)
    assert result.total == SUM_LIMIT * (SUM_LIMIT + 1) // 2
    print(f"Mode: {SUM_MODE}; N: {SUM_LIMIT}")
    print_compute_result(result)


if __name__ == "__main__":
    main()
```

## Lr2/lab_2/task2_async.py

```python
import asyncio
import ssl
import aiohttp
import certifi

from app.config import DEFAULT_WORKERS, REQUEST_TIMEOUT, URLS, split_items
from app.parsing import extract_title, run_and_print
from app.parse_shared import save_page_result


async def parse_and_save(url: str, session: aiohttp.ClientSession | None = None) -> bool:
    if session is None:
        connector = aiohttp.TCPConnector(ssl=ssl.create_default_context(cafile=certifi.where()))
        async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)) as client:
            return await parse_and_save(url, client)
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            title = extract_title(await response.read())
            await asyncio.to_thread(save_page_result, url, title, response.status, "async")
            print(f"[async] {response.status} | {url} | {title}", flush=True)
            return True
    except Exception as error:
        print(f"[async] ERROR | {url} | {type(error).__name__}: {error}", flush=True)
        return False


def main() -> None:
    chunks = split_items(URLS, DEFAULT_WORKERS)

    async def run_async() -> int:
        connector = aiohttp.TCPConnector(ssl=ssl.create_default_context(cafile=certifi.where()))
        async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)) as session:
            async def process_chunk(urls: list[str]) -> int:
                return sum([await parse_and_save(url, session) for url in urls])
            return sum(await asyncio.gather(*(process_chunk(chunk) for chunk in chunks)))

    run_and_print("async", len(URLS), lambda: asyncio.run(run_async()))


if __name__ == "__main__":
    main()
```

## Lr2/lab_2/task2_multiprocessing.py

```python
from multiprocessing import Pool
from app.config import DEFAULT_WORKERS, URLS, split_items
from app.parsing import fetch_and_save, run_and_print


def parse_and_save(url: str) -> bool:
    return fetch_and_save(url, "multiprocessing")


def process_chunk(urls: list[str]) -> int:
    return sum(parse_and_save(url) for url in urls)


def main() -> None:
    chunks = split_items(URLS, DEFAULT_WORKERS)

    def runner() -> int:
        with Pool(processes=len(chunks)) as pool:
            return sum(pool.map(process_chunk, chunks))

    run_and_print("multiprocessing", len(URLS), runner)


if __name__ == "__main__":
    main()
```

## Lr2/lab_2/task2_threading.py

```python
import threading
from app.config import DEFAULT_WORKERS, URLS, split_items
from app.parsing import fetch_and_save, run_and_print


def parse_and_save(url: str) -> bool:
    return fetch_and_save(url, "threading")


def main() -> None:
    chunks = split_items(URLS, DEFAULT_WORKERS)
    results = [0] * len(chunks)

    def worker(index: int, urls: list[str]) -> None:
        results[index] = sum(parse_and_save(url) for url in urls)

    def runner() -> int:
        threads = [threading.Thread(target=worker, args=(i, urls)) for i, urls in enumerate(chunks)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        return sum(results)

    run_and_print("threading", len(URLS), runner)


if __name__ == "__main__":
    main()
```
