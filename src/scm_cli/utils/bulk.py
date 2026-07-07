"""Bounded-concurrency runner for bulk operations (load commands).

Bulk YAML loads previously issued API calls one object at a time; with the
upsert pattern (fetch + create/update) that meant 2N sequential roundtrips
for N objects. `run_bulk` runs the per-item work in a small thread pool —
results keep input order and per-item exceptions are captured, so callers
report outcomes exactly as before.

Worker count: min(SCM_BULK_WORKERS (default 5), number of items).
"""

import os
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, TypeVar

T = TypeVar("T")

DEFAULT_WORKERS = 5


def _worker_count(item_count: int, max_workers: int | None) -> int:
    if max_workers is None:
        try:
            max_workers = int(os.environ.get("SCM_BULK_WORKERS", str(DEFAULT_WORKERS)))
        except ValueError:
            max_workers = DEFAULT_WORKERS
    return max(1, min(max_workers, item_count))


def run_bulk(
    items: Sequence[T],
    worker: Callable[[T], Any],
    max_workers: int | None = None,
) -> list[tuple[T, Any, Exception | None]]:
    """Run worker(item) for every item with bounded concurrency.

    Returns a list aligned with the input order: ``(item, result, exception)``
    per item, where exactly one of result/exception is set.
    """
    if not items:
        return []

    results: list[tuple[T, Any, Exception | None]] = [None] * len(items)  # type: ignore[list-item]
    with ThreadPoolExecutor(max_workers=_worker_count(len(items), max_workers)) as executor:
        futures = {executor.submit(worker, item): index for index, item in enumerate(items)}
        for future in as_completed(futures):
            index = futures[future]
            try:
                results[index] = (items[index], future.result(), None)
            except Exception as e:  # per-item failures are data, not control flow
                results[index] = (items[index], None, e)
    return results
