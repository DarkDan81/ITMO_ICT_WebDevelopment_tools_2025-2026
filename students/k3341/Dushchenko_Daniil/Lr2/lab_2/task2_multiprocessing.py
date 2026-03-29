from multiprocessing import Pool, cpu_count

import requests

from app.config import DEFAULT_WORKERS, URLS
from app.parse_shared import (
    extract_title,
    print_page_result,
    print_parse_result,
    reset_results,
    save_page_result,
    timed_parse_run,
)

FETCH_METHOD = "multiprocessing"


def parse_and_save(url: str) -> int:
    response = requests.get(url, timeout=20)
    title = extract_title(response.text)
    save_page_result(url, title, response.status_code, FETCH_METHOD)
    print_page_result(url, title, response.status_code, FETCH_METHOD)
    return 1


def main() -> None:
    reset_results(FETCH_METHOD)
    workers = min(DEFAULT_WORKERS, cpu_count(), len(URLS))

    def runner() -> int:
        with Pool(processes=workers) as pool:
            return sum(pool.map(parse_and_save, URLS))

    result = timed_parse_run(FETCH_METHOD, runner)
    print_parse_result(result)


if __name__ == "__main__":
    main()
