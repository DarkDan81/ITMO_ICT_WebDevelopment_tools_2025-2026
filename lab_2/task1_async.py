import asyncio

from app.compute_shared import calculate_sum, print_compute_result, split_range, timed_run
from app.config import DEFAULT_WORKERS, SUM_LIMIT


async def calculate_sum_async(start: int, end: int) -> int:
    await asyncio.sleep(0)
    return calculate_sum(start, end)


def main() -> None:
    workers = DEFAULT_WORKERS
    ranges = split_range(SUM_LIMIT, workers)

    def runner() -> int:
        async def run_async() -> int:
            tasks = [calculate_sum_async(start, end) for start, end in ranges]
            return sum(await asyncio.gather(*tasks))

        return asyncio.run(run_async())

    result = timed_run("asyncio", workers, runner)
    print_compute_result(result)


if __name__ == "__main__":
    main()
