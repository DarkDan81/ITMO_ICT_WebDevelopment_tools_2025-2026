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
