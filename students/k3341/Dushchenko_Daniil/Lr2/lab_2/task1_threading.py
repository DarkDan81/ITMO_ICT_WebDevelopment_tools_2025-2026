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
