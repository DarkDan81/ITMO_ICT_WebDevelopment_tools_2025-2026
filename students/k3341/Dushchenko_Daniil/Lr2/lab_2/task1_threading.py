from concurrent.futures import ThreadPoolExecutor

from app.compute_shared import calculate_sum, print_compute_result, split_range, timed_run
from app.config import DEFAULT_WORKERS, SUM_LIMIT


def main() -> None:
    workers = DEFAULT_WORKERS
    ranges = split_range(SUM_LIMIT, workers)

    def runner() -> int:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            return sum(executor.map(lambda bounds: calculate_sum(*bounds), ranges))

    result = timed_run("threading", workers, runner)
    print_compute_result(result)


if __name__ == "__main__":
    main()
