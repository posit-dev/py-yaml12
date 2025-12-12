from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Callable

import pytest

import yaml12

PROGRESS_TIMEOUT = 0.2
ITEM_COUNT = 2_000_000


@pytest.fixture(scope="module")
def large_yaml_text() -> str:
    return "".join(f"- {i}\n" for i in range(ITEM_COUNT))


@pytest.fixture(scope="module")
def large_yaml_path(tmp_path_factory, large_yaml_text: str) -> Path:
    path = tmp_path_factory.mktemp("gil_release") / "large.yaml"
    path.write_text(large_yaml_text, encoding="utf-8")
    return path


def _assert_other_thread_runs_while_parsing(work: Callable[[], None]) -> float:
    start_evt = threading.Event()
    progress_evt = threading.Event()
    done_evt = threading.Event()
    duration_holder: dict[str, float] = {}

    def worker():
        start_evt.set()
        t0 = time.perf_counter()
        try:
            work()
        finally:
            duration_holder["duration"] = time.perf_counter() - t0
            done_evt.set()

    def observer():
        start_evt.wait()
        progress_evt.set()

    parse_thread = threading.Thread(target=worker)
    observer_thread = threading.Thread(target=observer)
    parse_thread.start()
    observer_thread.start()

    progressed = progress_evt.wait(timeout=PROGRESS_TIMEOUT)

    parse_thread.join(timeout=10)
    observer_thread.join(timeout=10)

    duration = duration_holder.get("duration", 0.0)
    if duration < PROGRESS_TIMEOUT:
        pytest.skip(
            f"parse finished too quickly to assert GIL release (duration={duration:.3f}s)"
        )

    assert done_evt.is_set(), "parse thread did not finish in time"
    assert progressed, "other thread could not run while parse held the GIL"
    return duration


def test_parse_yaml_releases_gil_allows_thread_progress(large_yaml_text: str):
    duration = _assert_other_thread_runs_while_parsing(
        lambda: yaml12.parse_yaml(large_yaml_text)
    )
    assert duration >= PROGRESS_TIMEOUT


def test_read_yaml_releases_gil_allows_thread_progress(large_yaml_path: Path):
    duration = _assert_other_thread_runs_while_parsing(
        lambda: yaml12.read_yaml(large_yaml_path)
    )
    assert duration >= PROGRESS_TIMEOUT
