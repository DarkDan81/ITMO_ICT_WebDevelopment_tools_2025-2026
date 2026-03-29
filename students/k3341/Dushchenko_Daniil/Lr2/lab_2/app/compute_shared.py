from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter


@dataclass
class ComputeResult:
    approach: str
    workers: int
    total: int
    duration: float


def calculate_sum(start: int, end: int) -> int:
    """Return the arithmetic progression sum for a chunk."""
    count = end - start + 1
    return (start + end) * count // 2


def split_range(limit: int, chunks: int) -> list[tuple[int, int]]:
    chunk_size = limit // chunks
    ranges: list[tuple[int, int]] = []
    start = 1

    for index in range(chunks):
        end = start + chunk_size - 1
        if index == chunks - 1:
            end = limit
        ranges.append((start, end))
        start = end + 1

    return ranges


def timed_run(approach: str, workers: int, runner) -> ComputeResult:
    started = perf_counter()
    total = runner()
    duration = perf_counter() - started
    return ComputeResult(
        approach=approach,
        workers=workers,
        total=total,
        duration=duration,
    )


def print_compute_result(result: ComputeResult) -> None:
    print(f"Approach: {result.approach}")
    print(f"Workers: {result.workers}")
    print(f"Total sum: {result.total}")
    print(f"Duration: {result.duration:.6f} seconds")
