from __future__ import annotations


def best_by_metric(rows: list[dict], metric: str, lower_is_better: bool) -> dict:
    if not rows:
        return {}
    key = (lambda r: r.get(metric, float("inf"))) if lower_is_better else (lambda r: r.get(metric, float("-inf")))
    return sorted(rows, key=key)[0]
