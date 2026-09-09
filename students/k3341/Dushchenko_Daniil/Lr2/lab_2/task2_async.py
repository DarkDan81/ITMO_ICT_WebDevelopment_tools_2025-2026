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
