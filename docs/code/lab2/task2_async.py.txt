import asyncio

import aiohttp

from app.config import DEFAULT_WORKERS, URLS
from app.parse_shared import (
    extract_title,
    print_page_result,
    print_parse_result,
    reset_results,
    save_page_result,
    timed_parse_run,
)

FETCH_METHOD = "async"


async def parse_and_save(url: str, session: aiohttp.ClientSession) -> int:
    async with session.get(url, timeout=20) as response:
        html = await response.text()
        title = extract_title(html)
        await asyncio.to_thread(save_page_result, url, title, response.status, FETCH_METHOD)
        print_page_result(url, title, response.status, FETCH_METHOD)
        return 1


def chunked(items: list[str], chunks: int) -> list[list[str]]:
    size = max(1, len(items) // chunks)
    return [items[index:index + size] for index in range(0, len(items), size)]


def main() -> None:
    reset_results(FETCH_METHOD)
    workers = min(DEFAULT_WORKERS, len(URLS))
    url_chunks = chunked(URLS, workers)

    def runner() -> int:
        async def run_async() -> int:
            async with aiohttp.ClientSession() as session:
                async def process_chunk(urls: list[str]) -> int:
                    total = 0
                    for url in urls:
                        total += await parse_and_save(url, session)
                    return total

                tasks = [process_chunk(chunk) for chunk in url_chunks]
                return sum(await asyncio.gather(*tasks))

        return asyncio.run(run_async())

    result = timed_parse_run(FETCH_METHOD, runner)
    print_parse_result(result)


if __name__ == "__main__":
    main()
