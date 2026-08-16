from collections import defaultdict


def test_duplicate_policy_exact_drop_except_first() -> None:
    rows = [
        {"timestamp": "t1", "open": "1", "high": "2", "low": "1", "close": "2", "volume": "10"},
        {"timestamp": "t1", "open": "1", "high": "2", "low": "1", "close": "2", "volume": "10"},
    ]
    d = defaultdict(list)
    for i, r in enumerate(rows, start=1):
        d[r["timestamp"]].append((i, r))
    exact_drop = set()
    for _, entries in d.items():
        if len(entries) > 1:
            keep = entries[0][0]
            for idx, _ in entries:
                if idx != keep:
                    exact_drop.add(idx)
    assert exact_drop == {2}
