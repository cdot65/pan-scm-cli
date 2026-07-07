"""Tests for the bounded-concurrency bulk runner (scm_cli.utils.bulk)."""

import threading
import time

from scm_cli.utils.bulk import run_bulk


class TestRunBulk:
    def test_results_preserve_input_order(self):
        def worker(n):
            time.sleep(0.01 if n % 2 else 0)
            return n * 10

        results = run_bulk([1, 2, 3, 4], worker)

        assert [(item, value) for item, value, _ in results] == [(1, 10), (2, 20), (3, 30), (4, 40)]
        assert all(exc is None for _, _, exc in results)

    def test_exceptions_captured_per_item(self):
        def worker(n):
            if n == 2:
                raise ValueError("bad item")
            return n

        results = run_bulk([1, 2, 3], worker)

        assert results[0][2] is None
        assert isinstance(results[1][2], ValueError)
        assert results[1][1] is None
        assert results[2][2] is None

    def test_runs_concurrently(self):
        active = {"now": 0, "max": 0}
        lock = threading.Lock()

        def worker(n):
            with lock:
                active["now"] += 1
                active["max"] = max(active["max"], active["now"])
            time.sleep(0.05)
            with lock:
                active["now"] -= 1
            return n

        start = time.monotonic()
        run_bulk(list(range(10)), worker, max_workers=5)
        elapsed = time.monotonic() - start

        assert active["max"] > 1, "workers never overlapped"
        assert elapsed < 0.45, f"took {elapsed:.2f}s — looks sequential (10 x 0.05s)"

    def test_empty_items(self):
        assert run_bulk([], lambda x: x) == []

    def test_worker_env_override(self, monkeypatch):
        monkeypatch.setenv("SCM_BULK_WORKERS", "1")
        order = []

        def worker(n):
            order.append(n)
            return n

        run_bulk([1, 2, 3], worker)
        assert order == [1, 2, 3]  # single worker executes in submission order
