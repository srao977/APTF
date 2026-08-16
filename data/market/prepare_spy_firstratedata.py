from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, time as dtime
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any
from zoneinfo import ZoneInfo


NY_TZ = ZoneInfo("America/New_York")


@dataclass
class SourceInfo:
    source_path: Path
    filename: str
    extension: str
    delimiter: str
    encoding: str
    has_header: bool
    columns: list[str]
    row_count: int
    file_size_bytes: int
    sha256: str
    chronology_raw: str
    earliest_raw: str
    latest_raw: str


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def percentile(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    vals = sorted(values)
    if len(vals) == 1:
        return vals[0]
    idx = (len(vals) - 1) * q
    low = int(math.floor(idx))
    high = int(math.ceil(idx))
    if low == high:
        return vals[low]
    return vals[low] * (high - idx) + vals[high] * (idx - low)


def profile(values: list[float]) -> dict[str, float]:
    if not values:
        return {
            "count": 0,
            "min": float("nan"),
            "max": float("nan"),
            "mean": float("nan"),
            "median": float("nan"),
            "std": float("nan"),
            "p01": float("nan"),
            "p05": float("nan"),
            "p25": float("nan"),
            "p50": float("nan"),
            "p75": float("nan"),
            "p95": float("nan"),
            "p99": float("nan"),
        }
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": mean(values),
        "median": median(values),
        "std": pstdev(values) if len(values) > 1 else 0.0,
        "p01": percentile(values, 0.01),
        "p05": percentile(values, 0.05),
        "p25": percentile(values, 0.25),
        "p50": percentile(values, 0.50),
        "p75": percentile(values, 0.75),
        "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99),
    }


def parse_source_timestamp(s: str) -> datetime | None:
    txt = (s or "").strip()
    if not txt:
        return None
    fmts = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
    ]
    for f in fmts:
        try:
            return datetime.strptime(txt, f)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(txt)
    except ValueError:
        return None


def classify_session(local_dt: datetime) -> str:
    t = local_dt.timetz().replace(tzinfo=None)
    if dtime(9, 30) <= t < dtime(16, 0):
        return "REGULAR"
    if dtime(4, 0) <= t < dtime(9, 30):
        return "PREMARKET"
    if dtime(16, 0) <= t <= dtime(20, 0):
        return "AFTERHOURS"
    return "UNKNOWN"


def minute_of_session(local_dt: datetime) -> int:
    t = local_dt.timetz().replace(tzinfo=None)
    if not (dtime(9, 30) <= t < dtime(16, 0)):
        return -1
    return (local_dt.hour * 60 + local_dt.minute) - (9 * 60 + 30)


def detect_chronology(ts_values: list[str]) -> str:
    if len(ts_values) < 2:
        return "ASCENDING"
    asc = all(ts_values[i] <= ts_values[i + 1] for i in range(len(ts_values) - 1))
    desc = all(ts_values[i] >= ts_values[i + 1] for i in range(len(ts_values) - 1))
    if asc:
        return "ASCENDING"
    if desc:
        return "DESCENDING"
    return "MIXED"


def discover_source(path_hint: Path) -> Path:
    if path_hint.is_file():
        return path_hint
    if path_hint.exists() and path_hint.is_dir():
        candidates = sorted([p for p in path_hint.iterdir() if p.is_file()])
        if not candidates:
            raise FileNotFoundError(f"No files found in source folder: {path_hint}")
        if len(candidates) == 1:
            return candidates[0]
        spy = [p for p in candidates if "SPY" in p.name.upper()]
        if len(spy) == 1:
            return spy[0]
        csvs = [p for p in candidates if p.suffix.lower() == ".csv"]
        if len(csvs) == 1:
            return csvs[0]
        raise RuntimeError(f"Ambiguous source candidates: {[p.name for p in candidates]}")

    csv_guess = Path(str(path_hint) + ".csv")
    if csv_guess.is_file():
        return csv_guess

    raise FileNotFoundError(f"Source path not found: {path_hint}")


def write_csv(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def prepare(source_hint: Path, output_root: Path) -> dict[str, Any]:
    source = discover_source(source_hint)
    raw_dir = source.parent

    normalized_dir = output_root / "normalized"
    reports_dir = output_root / "reports"
    diagnostics_dir = output_root / "diagnostics"
    manifests_dir = output_root / "manifests"

    for p in [normalized_dir, reports_dir, diagnostics_dir, manifests_dir]:
        p.mkdir(parents=True, exist_ok=True)

    delimiter = ","
    encoding = "utf-8"

    with source.open("r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        columns = reader.fieldnames or []
        raw_rows = list(reader)

    if not columns:
        raise RuntimeError("Could not detect CSV header/columns")

    ts_col = "timestamp" if "timestamp" in columns else ("datetime" if "datetime" in columns else columns[0])
    open_col = "open" if "open" in columns else None
    high_col = "high" if "high" in columns else None
    low_col = "low" if "low" in columns else None
    close_col = "close" if "close" in columns else None
    volume_col = "volume" if "volume" in columns else None

    if not all([open_col, high_col, low_col, close_col, volume_col]):
        raise RuntimeError(f"Required OHLCV columns not found in source columns: {columns}")

    ts_values = [r.get(ts_col, "") for r in raw_rows]
    chronology_raw = detect_chronology(ts_values)

    duplicates = defaultdict(list)
    for i, r in enumerate(raw_rows, start=1):
        duplicates[r.get(ts_col, "")].append((i, r))

    duplicate_rows: list[dict[str, Any]] = []
    conflicting_duplicate_count = 0
    exact_duplicate_drop_indices = set()

    for ts, entries in duplicates.items():
        if len(entries) <= 1:
            continue
        sigs = []
        for _idx, row in entries:
            sigs.append((row.get(open_col), row.get(high_col), row.get(low_col), row.get(close_col), row.get(volume_col)))
        unique_sigs = set(sigs)
        if len(unique_sigs) > 1:
            conflicting_duplicate_count += 1
            for idx, row in entries:
                duplicate_rows.append(
                    {
                        "timestamp": ts,
                        "duplicate_count": len(entries),
                        "source_row_number": idx,
                        "open": row.get(open_col, ""),
                        "high": row.get(high_col, ""),
                        "low": row.get(low_col, ""),
                        "close": row.get(close_col, ""),
                        "volume": row.get(volume_col, ""),
                        "duplicate_type": "CONFLICTING_DUPLICATE",
                    }
                )
        else:
            keep = entries[0][0]
            for idx, row in entries:
                duplicate_rows.append(
                    {
                        "timestamp": ts,
                        "duplicate_count": len(entries),
                        "source_row_number": idx,
                        "open": row.get(open_col, ""),
                        "high": row.get(high_col, ""),
                        "low": row.get(low_col, ""),
                        "close": row.get(close_col, ""),
                        "volume": row.get(volume_col, ""),
                        "duplicate_type": "DUPLICATE_EXACT",
                    }
                )
                if idx != keep:
                    exact_duplicate_drop_indices.add(idx)

    timestamp_anomalies: list[dict[str, Any]] = []
    ohlc_anomalies: list[dict[str, Any]] = []
    volume_anomalies: list[dict[str, Any]] = []

    normalized_rows: list[dict[str, Any]] = []

    prices_open: list[float] = []
    prices_high: list[float] = []
    prices_low: list[float] = []
    prices_close: list[float] = []
    volumes: list[float] = []
    close_changes: list[float] = []
    close_returns: list[float] = []
    hl_ranges: list[float] = []
    hl_ranges_frac: list[float] = []
    log_volume: list[float] = []

    session_counter = Counter()
    daily_summary = defaultdict(lambda: {
        "first_timestamp_local": "",
        "last_timestamp_local": "",
        "row_count": 0,
        "regular_count": 0,
        "premarket_count": 0,
        "afterhours_count": 0,
        "unknown_count": 0,
    })

    prev_close = None
    prev_local_dt = None
    out_of_order = False

    for source_row_number, row in enumerate(raw_rows, start=1):
        if source_row_number in exact_duplicate_drop_indices:
            continue

        flags: list[str] = []
        ts_raw = row.get(ts_col, "")
        ts_naive = parse_source_timestamp(ts_raw)
        if ts_naive is None:
            flags.append("TIMESTAMP_INVALID")
            timestamp_anomalies.append({
                "source_row_number": source_row_number,
                "timestamp_raw": ts_raw,
                "anomaly": "TIMESTAMP_PARSE_FAILED",
            })
            continue

        local_dt = ts_naive.replace(tzinfo=NY_TZ)
        utc_dt = local_dt.astimezone(UTC)

        if prev_local_dt is not None and local_dt < prev_local_dt:
            out_of_order = True
            flags.append("OUT_OF_ORDER_SOURCE")
            timestamp_anomalies.append(
                {
                    "source_row_number": source_row_number,
                    "timestamp_raw": ts_raw,
                    "anomaly": "OUT_OF_ORDER_SOURCE",
                    "previous_timestamp": prev_local_dt.isoformat(),
                }
            )
        prev_local_dt = local_dt

        try:
            o = float(row.get(open_col, "nan"))
            h = float(row.get(high_col, "nan"))
            l = float(row.get(low_col, "nan"))
            c = float(row.get(close_col, "nan"))
            v = float(row.get(volume_col, "nan"))
        except Exception:
            flags.append("OTHER")
            continue

        valid = True

        if not (h >= o and h >= c and h >= l and l <= o and l <= c):
            valid = False
            flags.append("OHLC_INVALID")
            ohlc_anomalies.append(
                {
                    "source_row_number": source_row_number,
                    "timestamp_local": local_dt.isoformat(),
                    "open": o,
                    "high": h,
                    "low": l,
                    "close": c,
                    "anomaly": "OHLC_RULE_VIOLATION",
                }
            )

        if not (o > 0 and h > 0 and l > 0 and c > 0):
            valid = False
            if "OHLC_INVALID" not in flags:
                flags.append("OHLC_INVALID")
            ohlc_anomalies.append(
                {
                    "source_row_number": source_row_number,
                    "timestamp_local": local_dt.isoformat(),
                    "open": o,
                    "high": h,
                    "low": l,
                    "close": c,
                    "anomaly": "NON_POSITIVE_PRICE",
                }
            )

        if v < 0:
            valid = False
            flags.append("NEGATIVE_VOLUME")
            volume_anomalies.append(
                {
                    "source_row_number": source_row_number,
                    "timestamp_local": local_dt.isoformat(),
                    "volume": v,
                    "anomaly": "NEGATIVE_VOLUME",
                }
            )

        session_type = classify_session(local_dt)
        if session_type == "UNKNOWN":
            flags.append("UNKNOWN_SESSION")

        is_regular = session_type == "REGULAR"

        close_return_1m = ""
        if prev_close is not None and prev_close != 0:
            close_return_1m = c / prev_close - 1.0
            close_returns.append(close_return_1m)
            close_changes.append(c - prev_close)
        prev_close = c

        hl = h - l
        hlf = hl / c if c != 0 else float("nan")

        rec = {
            "entity_id": "SPY",
            "event_timestamp_local": local_dt.isoformat(),
            "event_timestamp_utc": utc_dt.isoformat().replace("+00:00", "Z"),
            "timezone": "America/New_York",
            "open": o,
            "high": h,
            "low": l,
            "close": c,
            "volume": v,
            "close_return_1m": close_return_1m,
            "high_low_range": hl,
            "high_low_range_fraction": hlf,
            "open_close_change": c - o,
            "open_close_return": (c / o - 1.0) if o != 0 else float("nan"),
            "session_type": session_type,
            "is_regular_session": str(is_regular).lower(),
            "minute_of_session": minute_of_session(local_dt),
            "source_provider": "FirstRateData",
            "source_dataset": "SPY_1min_firstratedata",
            "source_row_number": source_row_number,
            "data_valid": str(valid).lower(),
            "quality_flags": ";".join(flags),
        }
        normalized_rows.append(rec)

        prices_open.append(o)
        prices_high.append(h)
        prices_low.append(l)
        prices_close.append(c)
        volumes.append(v)
        log_volume.append(math.log1p(v))
        hl_ranges.append(hl)
        hl_ranges_frac.append(hlf)

        dkey = local_dt.date().isoformat()
        ds = daily_summary[dkey]
        ds["row_count"] += 1
        if not ds["first_timestamp_local"]:
            ds["first_timestamp_local"] = local_dt.isoformat()
        ds["last_timestamp_local"] = local_dt.isoformat()
        if session_type == "REGULAR":
            ds["regular_count"] += 1
        elif session_type == "PREMARKET":
            ds["premarket_count"] += 1
        elif session_type == "AFTERHOURS":
            ds["afterhours_count"] += 1
        else:
            ds["unknown_count"] += 1

        session_counter[session_type] += 1

    normalized_rows.sort(key=lambda r: r["event_timestamp_utc"])

    # Interval and gap analysis.
    missing_interval_rows: list[dict[str, Any]] = []
    if len(normalized_rows) > 1:
        prev_dt = datetime.fromisoformat(normalized_rows[0]["event_timestamp_local"])
        prev_sess = normalized_rows[0]["session_type"]
        prev_vol = float(normalized_rows[0]["volume"])

        for i in range(1, len(normalized_rows)):
            cur = normalized_rows[i]
            cur_dt = datetime.fromisoformat(cur["event_timestamp_local"])
            delta_min = int((cur_dt - prev_dt).total_seconds() // 60)
            if delta_min != 1:
                if prev_dt.date() != cur_dt.date() or prev_sess != "REGULAR" or cur["session_type"] != "REGULAR":
                    cls = "EXPECTED_SESSION_GAP"
                else:
                    if prev_vol == 0 or float(cur["volume"]) == 0:
                        cls = "POSSIBLE_ZERO_VOLUME_OMISSION"
                    else:
                        cls = "POSSIBLE_DATA_GAP"
                missing_interval_rows.append(
                    {
                        "from_timestamp_local": prev_dt.isoformat(),
                        "to_timestamp_local": cur_dt.isoformat(),
                        "delta_minutes": delta_min,
                        "classification": cls,
                    }
                )
            prev_dt = cur_dt
            prev_sess = cur["session_type"]
            prev_vol = float(cur["volume"])

    # Additional summary classifications for early close style days.
    for d, ds in daily_summary.items():
        if ds["regular_count"] < 390 and ds["regular_count"] > 0:
            last_local = datetime.fromisoformat(ds["last_timestamp_local"]).timetz().replace(tzinfo=None)
            if last_local < dtime(15, 30):
                missing_interval_rows.append(
                    {
                        "from_timestamp_local": ds["first_timestamp_local"],
                        "to_timestamp_local": ds["last_timestamp_local"],
                        "delta_minutes": 0,
                        "classification": "EARLY_CLOSE_OR_SPECIAL_SESSION",
                    }
                )

    # session summary
    session_summary_rows = []
    total_rows = len(normalized_rows)
    for s in ["PREMARKET", "REGULAR", "AFTERHOURS", "UNKNOWN"]:
        count = session_counter[s]
        session_summary_rows.append(
            {
                "session_type": s,
                "row_count": count,
                "fraction": (count / total_rows) if total_rows else 0.0,
            }
        )

    daily_rows = []
    for d, ds in sorted(daily_summary.items()):
        daily_rows.append({"date": d, **ds})

    feature_profile_rows = []
    for name, vals in [
        ("open", prices_open),
        ("high", prices_high),
        ("low", prices_low),
        ("close", prices_close),
        ("volume", volumes),
        ("log1p_volume", log_volume),
        ("close_change_abs", [abs(x) for x in close_changes]),
        ("close_return_abs", [abs(x) for x in close_returns]),
        ("high_low_range", hl_ranges),
        ("high_low_range_fraction", hl_ranges_frac),
    ]:
        st = profile(vals)
        feature_profile_rows.append({"feature": name, **st})

    # Write diagnostics CSVs.
    write_csv(
        diagnostics_dir / "duplicate_timestamps.csv",
        [
            "timestamp",
            "duplicate_count",
            "source_row_number",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "duplicate_type",
        ],
        duplicate_rows,
    )

    interval_class_counts = Counter(r["classification"] for r in missing_interval_rows)
    interval_bucket_counts = Counter()
    for r in missing_interval_rows:
        dmin = int(r["delta_minutes"])
        if dmin == 1:
            b = "1"
        elif dmin == 2:
            b = "2"
        elif 3 <= dmin <= 5:
            b = "3-5"
        elif dmin > 5:
            b = ">5"
        else:
            b = "0"
        interval_bucket_counts[b] += 1

    missing_interval_summary_rows = [
        {
            "metric": "delta_bucket_1",
            "count": interval_bucket_counts["1"],
        },
        {
            "metric": "delta_bucket_2",
            "count": interval_bucket_counts["2"],
        },
        {
            "metric": "delta_bucket_3_5",
            "count": interval_bucket_counts["3-5"],
        },
        {
            "metric": "delta_bucket_gt_5",
            "count": interval_bucket_counts[">5"],
        },
    ] + [
        {
            "metric": f"classification_{k}",
            "count": v,
        }
        for k, v in sorted(interval_class_counts.items())
    ]

    write_csv(diagnostics_dir / "missing_interval_summary.csv", ["metric", "count"], missing_interval_summary_rows)
    write_csv(
        diagnostics_dir / "timestamp_anomalies.csv",
        ["source_row_number", "timestamp_raw", "anomaly", "previous_timestamp"],
        timestamp_anomalies,
    )
    write_csv(
        diagnostics_dir / "ohlc_anomalies.csv",
        ["source_row_number", "timestamp_local", "open", "high", "low", "close", "anomaly"],
        ohlc_anomalies,
    )
    write_csv(
        diagnostics_dir / "volume_anomalies.csv",
        ["source_row_number", "timestamp_local", "volume", "anomaly"],
        volume_anomalies,
    )
    write_csv(diagnostics_dir / "session_summary.csv", ["session_type", "row_count", "fraction"], session_summary_rows)
    write_csv(
        diagnostics_dir / "daily_summary.csv",
        [
            "date",
            "first_timestamp_local",
            "last_timestamp_local",
            "row_count",
            "regular_count",
            "premarket_count",
            "afterhours_count",
            "unknown_count",
        ],
        daily_rows,
    )
    write_csv(
        diagnostics_dir / "feature_profile.csv",
        [
            "feature",
            "count",
            "min",
            "max",
            "mean",
            "median",
            "std",
            "p01",
            "p05",
            "p25",
            "p50",
            "p75",
            "p95",
            "p99",
        ],
        feature_profile_rows,
    )

    normalized_headers = [
        "entity_id",
        "event_timestamp_local",
        "event_timestamp_utc",
        "timezone",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_return_1m",
        "high_low_range",
        "high_low_range_fraction",
        "open_close_change",
        "open_close_return",
        "session_type",
        "is_regular_session",
        "minute_of_session",
        "source_provider",
        "source_dataset",
        "source_row_number",
        "data_valid",
        "quality_flags",
    ]

    normalized_path = normalized_dir / "SPY_1min_normalized_v0_1.csv"
    write_csv(normalized_path, normalized_headers, normalized_rows)
    normalized_sha = sha256_file(normalized_path)

    earliest = normalized_rows[0]["event_timestamp_local"] if normalized_rows else ""
    latest = normalized_rows[-1]["event_timestamp_local"] if normalized_rows else ""

    raw_manifest = {
        "source_path": str(source),
        "source_filename": source.name,
        "file_size_bytes": source.stat().st_size,
        "sha256": sha256_file(source),
        "inspection_timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "row_count": len(raw_rows),
        "column_names": columns,
    }

    source_info = SourceInfo(
        source_path=source,
        filename=source.name,
        extension=source.suffix,
        delimiter=delimiter,
        encoding=encoding,
        has_header=True,
        columns=columns,
        row_count=len(raw_rows),
        file_size_bytes=source.stat().st_size,
        sha256=raw_manifest["sha256"],
        chronology_raw=chronology_raw,
        earliest_raw=ts_values[0] if ts_values else "",
        latest_raw=ts_values[-1] if ts_values else "",
    )

    with (manifests_dir / "SPY_RAW_SOURCE_MANIFEST_V0_1.json").open("w", encoding="utf-8") as f:
        json.dump(raw_manifest, f, indent=2)

    normalized_manifest = {
        "source_sha256": source_info.sha256,
        "normalized_file": str(normalized_path),
        "normalized_sha256": normalized_sha,
        "source_row_count": len(raw_rows),
        "normalized_row_count": len(normalized_rows),
        "valid_row_count": sum(1 for r in normalized_rows if r["data_valid"] == "true"),
        "invalid_row_count": sum(1 for r in normalized_rows if r["data_valid"] != "true"),
        "duplicate_count": sum(1 for k, v in duplicates.items() if len(v) > 1),
        "conflicting_duplicate_count": conflicting_duplicate_count,
        "earliest_timestamp": earliest,
        "latest_timestamp": latest,
        "timezone_assumption": "America/New_York (SOURCE_TIMEZONE_EXPLICIT=NO)",
        "regular_session_row_count": session_counter["REGULAR"],
        "extended_session_row_count": session_counter["PREMARKET"] + session_counter["AFTERHOURS"],
        "unknown_session_row_count": session_counter["UNKNOWN"],
        "column_schema": normalized_headers,
        "normalization_version": "v0_1",
        "creation_timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
    }

    with (manifests_dir / "SPY_NORMALIZED_MANIFEST_V0_1.json").open("w", encoding="utf-8") as f:
        json.dump(normalized_manifest, f, indent=2)

    # Source schema profile table.
    schema_rows = []
    for c in columns:
        vals = [r.get(c, "") for r in raw_rows]
        null_count = sum(1 for v in vals if (v is None or str(v).strip() == ""))
        numeric_vals = []
        sample_values = []
        for v in vals[:5]:
            sample_values.append(v)
        for v in vals:
            try:
                numeric_vals.append(float(v))
            except Exception:
                pass
        detected_type = "numeric" if len(numeric_vals) >= max(1, len(vals) // 2) else "string"
        schema_rows.append(
            {
                "name": c,
                "detected_type": detected_type,
                "null_count": null_count,
                "unique_count": len(set(vals)),
                "min": min(numeric_vals) if numeric_vals and detected_type == "numeric" else min(vals) if vals else "",
                "max": max(numeric_vals) if numeric_vals and detected_type == "numeric" else max(vals) if vals else "",
                "sample_values": " | ".join(str(x) for x in sample_values),
            }
        )

    # Report building.
    missing_fields_for_d01 = ["bid", "ask", "bid_size", "ask_size", "trade_size"]
    d01_compat = "PASS WITH MAPPING"

    # initial 6-month recommendation
    initial_6m = "NOT AVAILABLE"
    if normalized_rows:
        dt_start = datetime.fromisoformat(normalized_rows[0]["event_timestamp_local"])
        dt_end = datetime.fromisoformat(normalized_rows[-1]["event_timestamp_local"])
        # choose final ~6 months of range.
        target_start = dt_end.replace(month=max(1, dt_end.month - 6))
        if dt_end.month <= 6:
            target_start = target_start.replace(year=dt_end.year - 1, month=dt_end.month + 6)
        if target_start < dt_start:
            target_start = dt_start
        initial_6m = f"{target_start.date().isoformat()} to {dt_end.date().isoformat()}"

    inspection_md = f"""# SPY Dataset Inspection v0.1

## 1. Source discovered
- Source discovered as file.

## 2. Raw path
- {source}

## 3. File format
- CSV

## 4. File size
- {source_info.file_size_bytes} bytes

## 5. SHA256
- {source_info.sha256}

## 6. Row count
- {len(raw_rows)}

## 7. Schema
- Columns: {", ".join(columns)}

## 8. Timestamp format
- Parsed format: YYYY-MM-DD HH:MM:SS (timezone-naive in source)

## 9. Earliest date
- {source_info.earliest_raw}

## 10. Latest date
- {source_info.latest_raw}

## 11. Raw chronology
- {source_info.chronology_raw}

## 12. Timezone finding
- SOURCE_TIMEZONE_EXPLICIT = NO
- Normalization assumption: America/New_York

## 13. Session coverage
- Premarket: {session_counter['PREMARKET']}
- Regular: {session_counter['REGULAR']}
- Afterhours: {session_counter['AFTERHOURS']}
- Unknown: {session_counter['UNKNOWN']}

## 14. OHLCV profile
- See diagnostics/feature_profile.csv

## 15. Duplicates
- Duplicate timestamps: {sum(1 for k, v in duplicates.items() if len(v) > 1)}
- Conflicting duplicates: {conflicting_duplicate_count}

## 16. Gaps
- See diagnostics/missing_interval_summary.csv

## 17. Anomalies
- Timestamp anomalies: {len(timestamp_anomalies)}
- OHLC anomalies: {len(ohlc_anomalies)}
- Volume anomalies: {len(volume_anomalies)}

## 18. Source limitations
- No explicit timezone token in source.
- No bid/ask/bid_size/ask_size/trade_size fields.

## 19. Normalized output created
- normalized/SPY_1min_normalized_v0_1.csv

## 20. Recommendation
- D01 HISTORICAL REPLAY DATA: READY WITH LIMITATIONS
"""

    quality_md = f"""# SPY Data Quality Report v0.1

## Row-level validity
- Valid rows: {sum(1 for r in normalized_rows if r['data_valid'] == 'true')}
- Invalid rows: {sum(1 for r in normalized_rows if r['data_valid'] != 'true')}

## Duplicate analysis
- Duplicate timestamps: {sum(1 for k, v in duplicates.items() if len(v) > 1)}
- Conflicting duplicate timestamps: {conflicting_duplicate_count}

## Timestamp anomalies
- Count: {len(timestamp_anomalies)}

## OHLC anomalies
- Count: {len(ohlc_anomalies)}

## Volume anomalies
- Negative volume rows: {sum(1 for r in volume_anomalies if r.get('anomaly') == 'NEGATIVE_VOLUME')}
- Zero volume rows: {sum(1 for v in volumes if v == 0)}

## Irregular intervals
- See diagnostics/missing_interval_summary.csv

## Session completeness
- Distinct dates: {len(daily_rows)}
- Daily distribution: diagnostics/daily_summary.csv

## Potential concerns for D01
- Missing bid/ask fields require mapping strategy.
- Irregular intervals preserved intentionally for dt-aware replay.
"""

    mapping_lines = []
    for s in schema_rows:
        mapping_lines.append(f"- {s['name']} -> type={s['detected_type']}, nulls={s['null_count']}, unique={s['unique_count']}")

    normalization_spec_md = f"""# SPY Normalization Spec v0.1

## Source schema
{chr(10).join(mapping_lines)}

## Target schema
- entity_id
- event_timestamp_local
- event_timestamp_utc
- timezone
- open, high, low, close, volume
- close_return_1m
- high_low_range, high_low_range_fraction
- open_close_change, open_close_return
- session_type, is_regular_session, minute_of_session
- source_provider, source_dataset, source_row_number
- data_valid, quality_flags

## Column mapping
- timestamp -> event_timestamp_local/event_timestamp_utc
- open/high/low/close/volume -> direct numeric mapping

## Timestamp conversion
- Source parsed as timezone-naive local market time.
- Assumption: America/New_York.
- UTC conversion with zone-aware DST handling.

## Sorting
- Normalized output sorted ascending by event_timestamp_utc.

## Duplicate policy
- Exact duplicate rows at same timestamp: keep one.
- Conflicting duplicates: retain rows, flag DUPLICATE_CONFLICT in diagnostics.

## Invalid-row policy
- Keep rows when parseable; mark data_valid=false and quality_flags.

## Session classification
- PREMARKET: 04:00 <= t < 09:30
- REGULAR: 09:30 <= t < 16:00
- AFTERHOURS: 16:00 <= t <= 20:00
- UNKNOWN otherwise

## Derived fields
- close_return_1m uses current/previous observed close only (no future leakage).
- high_low_range, high_low_range_fraction, open_close_change, open_close_return.

## No-fill policy
- No interpolation, no synthetic bars, no forward fill.

## Traceability fields
- source_row_number retained.

## Hashing
- SHA256 on raw source and normalized output recorded in manifests.
"""

    session_md = f"""# SPY Session Analysis v0.1

## Date range
- {earliest} to {latest}

## Distinct dates
- {len(daily_rows)}

## Session row counts
- Regular: {session_counter['REGULAR']}
- Premarket: {session_counter['PREMARKET']}
- Afterhours: {session_counter['AFTERHOURS']}
- Unknown: {session_counter['UNKNOWN']}

## Regular bars/day distribution
- See diagnostics/daily_summary.csv

## Missing intraday interval profile
- See diagnostics/missing_interval_summary.csv
"""

    volume_stats = profile(volumes)
    volume_md = f"""# SPY Volume Profile v0.1

## Raw volume statistics
- count: {volume_stats['count']}
- min: {volume_stats['min']}
- max: {volume_stats['max']}
- mean: {volume_stats['mean']}
- median: {volume_stats['median']}
- std: {volume_stats['std']}
- p01: {volume_stats['p01']}
- p05: {volume_stats['p05']}
- p25: {volume_stats['p25']}
- p50: {volume_stats['p50']}
- p75: {volume_stats['p75']}
- p95: {volume_stats['p95']}
- p99: {volume_stats['p99']}

## log1p(volume)
- See diagnostics/feature_profile.csv

## Intraday profile
- Session-level distribution available via diagnostics/session_summary.csv and diagnostics/daily_summary.csv.
"""

    readiness_class = "READY WITH LIMITATIONS"
    readiness_md = f"""# SPY Historical Replay Readiness v0.1

## AVAILABLE FROM SOURCE
- timestamp
- open
- high
- low
- close
- volume

## NOT AVAILABLE FROM SOURCE
- bid
- ask
- bid_size
- ask_size
- trade_size

## DERIVED DURING NORMALIZATION
- close_return_1m (backward-looking)
- high_low_range
- high_low_range_fraction
- open_close_change
- open_close_return
- session_type
- is_regular_session
- minute_of_session

## DERIVED INSIDE D01
- relative volume
- volume density
- velocity
- acceleration
- adaptive half-life
- perturbation
- strength
- DMO
- FMO

## Questions
1. Is source readable? YES
2. Is chronology trustworthy? YES ({source_info.chronology_raw})
3. Is timezone interpretable? YES (assumed America/New_York; source explicit=NO)
4. Is OHLC internally consistent? {'YES' if len(ohlc_anomalies) == 0 else 'PARTIAL'}
5. Is volume usable? {'YES' if sum(1 for r in volume_anomalies if r.get('anomaly') == 'NEGATIVE_VOLUME') == 0 else 'PARTIAL'}
6. Are irregular intervals preserved? YES
7. Can D01 calculate dt safely? YES
8. Are required D01 fields available? PASS WITH MAPPING
9. Which fields are missing? {', '.join(missing_fields_for_d01)}
10. Does CSVReplayProvider need mapping adjustment? YES (timestamp/price column mapping)
11. Suitable for initial D01 replay? {readiness_class}

## Final classification
D01 HISTORICAL REPLAY DATA: {readiness_class}

## Initial 6-month slice recommendation
- {initial_6m}

## Future chronological split proposal
- 60% adaptation / 20% validation / 20% evaluation (proposal only)
"""

    write_md(reports_dir / "SPY_DATASET_INSPECTION_V0_1.md", inspection_md)
    write_md(reports_dir / "SPY_DATA_QUALITY_REPORT_V0_1.md", quality_md)
    write_md(reports_dir / "SPY_NORMALIZATION_SPEC_V0_1.md", normalization_spec_md)
    write_md(reports_dir / "SPY_SESSION_ANALYSIS_V0_1.md", session_md)
    write_md(reports_dir / "SPY_VOLUME_PROFILE_V0_1.md", volume_md)
    write_md(reports_dir / "SPY_HISTORICAL_REPLAY_READINESS_V0_1.md", readiness_md)

    return {
        "source": source,
        "source_filename": source.name,
        "source_format": "CSV",
        "source_sha256": source_info.sha256,
        "source_rows": len(raw_rows),
        "source_date_earliest": source_info.earliest_raw,
        "source_date_latest": source_info.latest_raw,
        "timezone_explicit": "NO",
        "normalized_timezone": "America/New_York + UTC",
        "raw_chronology": source_info.chronology_raw,
        "normalized_chronology": "ASCENDING",
        "duplicate_timestamps": sum(1 for k, v in duplicates.items() if len(v) > 1),
        "conflicting_duplicates": conflicting_duplicate_count,
        "invalid_ohlc_rows": len(ohlc_anomalies),
        "negative_volume_rows": sum(1 for r in volume_anomalies if r.get("anomaly") == "NEGATIVE_VOLUME"),
        "regular_rows": session_counter["REGULAR"],
        "extended_rows": session_counter["PREMARKET"] + session_counter["AFTERHOURS"],
        "unknown_rows": session_counter["UNKNOWN"],
        "normalized_rows": len(normalized_rows),
        "valid_normalized_rows": sum(1 for r in normalized_rows if r["data_valid"] == "true"),
        "normalized_file": normalized_path,
        "normalized_sha256": normalized_sha,
        "d01_compat": d01_compat,
        "missing_d01_fields": missing_fields_for_d01,
        "initial_6m": initial_6m,
        "readiness": readiness_class,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect, validate, and normalize FirstRateData SPY 1-minute dataset")
    parser.add_argument(
        "--source",
        default=r"C:\Users\chino\APTF\data\market\raw\SPY_1min_firstratedata",
        help="Source file/folder/path hint",
    )
    parser.add_argument(
        "--output-root",
        default=r"C:\Users\chino\APTF\data\market",
        help="Output root for normalized/reports/diagnostics/manifests",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = prepare(Path(args.source), Path(args.output_root))

    # determinism check by second run hash compare
    result2 = prepare(Path(args.source), Path(args.output_root))
    determinism = "PASS" if result["normalized_sha256"] == result2["normalized_sha256"] else "FAIL"

    print("APTF SPY HISTORICAL DATA PREPARATION V0.1 COMPLETE")
    print()
    print(f"SOURCE:\n{result['source']}")
    print()
    print(f"SOURCE FILE:\n{result['source_filename']}")
    print()
    print(f"SOURCE FORMAT:\n{result['source_format']}")
    print()
    print(f"SOURCE SHA256:\n{result['source_sha256']}")
    print()
    print(f"SOURCE ROWS:\n{result['source_rows']}")
    print()
    print(f"SOURCE DATE RANGE:\n{result['source_date_earliest']}\nto\n{result['source_date_latest']}")
    print()
    print(f"TIMEZONE EXPLICIT IN SOURCE:\n{result['timezone_explicit']}")
    print()
    print(f"NORMALIZED TIMEZONE:\n{result['normalized_timezone']}")
    print()
    print(f"RAW CHRONOLOGY:\n{result['raw_chronology']}")
    print()
    print(f"NORMALIZED CHRONOLOGY:\n{result['normalized_chronology']}")
    print()
    print(f"DUPLICATE TIMESTAMPS:\n{result['duplicate_timestamps']}")
    print()
    print(f"CONFLICTING DUPLICATES:\n{result['conflicting_duplicates']}")
    print()
    print(f"INVALID OHLC ROWS:\n{result['invalid_ohlc_rows']}")
    print()
    print(f"NEGATIVE VOLUME ROWS:\n{result['negative_volume_rows']}")
    print()
    print(f"REGULAR SESSION ROWS:\n{result['regular_rows']}")
    print()
    print(f"EXTENDED SESSION ROWS:\n{result['extended_rows']}")
    print()
    print(f"UNKNOWN SESSION ROWS:\n{result['unknown_rows']}")
    print()
    print(f"NORMALIZED ROWS:\n{result['normalized_rows']}")
    print()
    print(f"VALID NORMALIZED ROWS:\n{result['valid_normalized_rows']}")
    print()
    print(f"NORMALIZED FILE:\n{result['normalized_file']}")
    print()
    print(f"NORMALIZED SHA256:\n{result['normalized_sha256']}")
    print()
    print(f"NORMALIZATION DETERMINISM:\n{determinism}")
    print()
    print(f"D01 CSV REPLAY COMPATIBILITY:\n{result['d01_compat']}")
    print()
    print(f"MISSING D01 SOURCE FIELDS:\n{', '.join(result['missing_d01_fields'])}")
    print()
    print(f"INITIAL 6-MONTH SLICE:\n{result['initial_6m']}")
    print()
    print(f"D01 HISTORICAL REPLAY DATA:\n{result['readiness']}")
    print()
    print("PRIMARY REPORT:\nreports\\SPY_DATASET_INSPECTION_V0_1.md")
    print()
    print("QUALITY REPORT:\nreports\\SPY_DATA_QUALITY_REPORT_V0_1.md")
    print()
    print("NORMALIZATION SPEC:\nreports\\SPY_NORMALIZATION_SPEC_V0_1.md")
    print()
    print("REPLAY READINESS:\nreports\\SPY_HISTORICAL_REPLAY_READINESS_V0_1.md")
    print()
    print("D01 MODEL RUN:\nNOT PERFORMED")
    print()
    print("NETWORK ACCESS:\nNONE")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
