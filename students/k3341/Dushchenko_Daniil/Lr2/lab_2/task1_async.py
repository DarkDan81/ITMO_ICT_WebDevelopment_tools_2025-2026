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
