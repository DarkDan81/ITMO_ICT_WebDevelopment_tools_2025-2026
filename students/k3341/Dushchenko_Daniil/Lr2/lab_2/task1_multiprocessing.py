from multiprocessing import Pool, cpu_count

from app.compute_shared import calculate_sum, print_compute_result, split_range, timed_run
from app.config import DEFAULT_WORKERS, SUM_LIMIT


def _calculate_chunk(bounds: tuple[int, int]) -> int:
    return calculate_sum(*bounds)


def main() -> None:
    workers = min(DEFAULT_WORKERS, cpu_count())
    ranges = split_range(SUM_LIMIT, workers)

    def runner() -> int:
        with Pool(processes=workers) as pool:
            return sum(pool.map(_calculate_chunk, ranges))

    result = timed_run("multiprocessing", workers, runner)
    print_compute_result(result)


if __name__ == "__main__":
    main()
