from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, datetime
import os
from pathlib import Path
import time
from typing import Any

from .constants import DIMENSIONS
from .evidence import read_anchor_jsonl
from .scoring import score_dimension


def _worker(task: dict[str, Any]) -> dict[str, Any]:
    started = datetime.now(UTC)
    begin = time.perf_counter()
    begin_ns = time.perf_counter_ns()
    if task.get("smoke_delay"):
        time.sleep(float(task["smoke_delay"]))
    result = None
    evidence_path = task.get("evidence_path")
    if evidence_path:
        records = read_anchor_jsonl(Path(evidence_path))
        result = score_dimension(task["dimension"], records, int(task["replicates"]))
    end_ns = time.perf_counter_ns()
    return {
        "task_id": task["task_id"], "dimension": task["dimension"], "pid": os.getpid(),
        "parent_pid": os.getppid(), "start_utc": started.isoformat(),
        "end_utc": datetime.now(UTC).isoformat(), "elapsed_seconds": time.perf_counter() - begin,
        "monotonic_start_ns": begin_ns, "monotonic_end_ns": end_ns,
        "status": "PASS", "record_count": int(task.get("record_count", 0)), "result": result,
    }


def _measured_peak(results: list[dict[str, Any]]) -> int:
    events = []
    for result in results:
        events.append((int(result["monotonic_start_ns"]), 1))
        events.append((int(result["monotonic_end_ns"]), -1))
    active = peak = 0
    for _, delta in sorted(events, key=lambda item: (item[0], item[1])):
        active += delta
        peak = max(peak, active)
    return peak


def run_evidence_tasks(record_count: int, max_workers: int | None = None, smoke_delay: float = 0.0, evidence_path: str | None = None, replicates: int = 2000) -> dict[str, object]:
    workers = max_workers or min(18, os.cpu_count() or 1)
    tasks = [{"task_id": f"TASK-{index:02d}", "dimension": dimension, "record_count": record_count, "smoke_delay": smoke_delay, "evidence_path": evidence_path, "replicates": replicates} for index, dimension in enumerate(DIMENSIONS, start=1)]
    results: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(_worker, task) for task in tasks]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda item: item["task_id"])
    unique_workers = len({item["pid"] for item in results})
    return {"max_workers": workers, "unique_worker_count": unique_workers, "peak_concurrency": _measured_peak(results), "failures": 0, "mode": "dimension_scoring" if evidence_path else "process_smoke", "tasks": results}