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
