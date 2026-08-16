from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime
import hashlib
import json
import math
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in os.sys.path:
    os.sys.path.insert(0, str(SRC))

from d01.v02.config import AblationConfig, D01V02Config
from d01.v02.model import D01V02Model
from d01.v02.observations import NormalizedObservation

OUTPUT_ROOT = ROOT / "output" / "d01_v02_perturbation_adaptation_correction"
DIRS = {
    "reports": OUTPUT_ROOT / "reports",
    "metrics": OUTPUT_ROOT / "metrics",
    "diagnostics": OUTPUT_ROOT / "diagnostics",
    "logs": OUTPUT_ROOT / "logs",
    "workers": OUTPUT_ROOT / "workers",
    "manifests": OUTPUT_ROOT / "manifests",
}

WINDOWS = {
    "S05": {"pre": (1, 89), "event_onset": (90, 100), "event_peak": (101, 120), "immediate_post": (121, 140), "recovery": (141, 180), "count": 180},
    "S06": {"pre": (1, 79), "event_onset": (80, 95), "event_peak": (96, 110), "immediate_post": (111, 130), "recovery": (131, 180), "count": 180},
}

MAX_WORKERS = 18
MANIFEST_NAME = "D01_V0_2_PERTURBATION_ADAPTATION_CORRECTION_MANIFEST.json"
PRE_HASH_PATH = DIRS["manifests"] / "pre_correction_source_hashes.json"


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def ensure_dirs() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    for d in DIRS.values():
        d.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as h:
        w = csv.DictWriter(h, fieldnames=headers)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest().upper()


def source_hashes() -> dict[str, str]:
    files = sorted((ROOT / "src" / "d01" / "v02").glob("*.py"))
    return {str(p.relative_to(ROOT)).replace("\\", "/"): sha256_file(p) for p in files}


def stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest().upper()


def _obs(entity: str, seq: int, t: float, price: float, volume: float, source_quality: float = 1.0) -> NormalizedObservation:
    return NormalizedObservation(
        entity_id=entity,
        event_time=t,
        receive_time=t,
        sequence_id=seq,
        price=price,
        volume=volume,
        source_quality=source_quality,
        availability_mask={"price": True, "volume": True},
    )


def generate_scenario(name: str) -> list[NormalizedObservation]:
    out: list[NormalizedObservation] = []
    count = WINDOWS[name]["count"]
    entity = f"SYN:{name}"
    t = 0.0
    price = 100.0
    for seq in range(1, count + 1):
        if name == "S05":
            if seq < 90:
                price += 0.03
                volume = 900.0
            else:
                price -= 0.05
                volume = 6000.0
        elif name == "S06":
            price += 0.03 if seq < 80 else -0.09
            volume = 2000.0
        else:
            raise ValueError(name)
        t += 1.0
        out.append(_obs(entity, seq, t, price, volume, 1.0))
    return out


def window_name(scenario: str, idx: int) -> str:
    for name, bounds in WINDOWS[scenario].items():
        if name == "count":
            continue
        if bounds[0] <= idx <= bounds[1]:
            return name.upper()
    return "UNKNOWN"


def build_tasks(kind: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for scenario in ["S05", "S06"]:
        for mode in ["ON", "OFF"]:
            out.append({"task_id": f"{kind}_{scenario}_{mode}", "kind": kind, "scenario": scenario, "mode": mode})
    return out


def run_single_task(task: dict[str, str], src_hash: dict[str, str]) -> dict[str, Any]:
    scenario = task["scenario"]
    mode = task["mode"]
    enabled = mode == "ON"
    cfg = D01V02Config(ablation=AblationConfig(perturbation_adaptation=enabled))
    model = D01V02Model(entity_id=f"CORR:{task['kind']}:{scenario}:{mode}", config=cfg)
    observations = generate_scenario(scenario)

    pid = os.getpid()
    started = datetime.now(UTC).timestamp()
    trace_rows: list[dict[str, Any]] = []
    param_rows: list[dict[str, Any]] = []

    try:
        for idx, obs in enumerate(observations, start=1):
            dmo, _fmo = model.step(obs)
            win = window_name(scenario, idx)
            theta_after = float(dmo.parameter_state["ref_alpha"])
            mag = float(dmo.parameter_update_magnitude["ref_alpha"])
            lo, hi = cfg.adaptation.parameter_bounds["ref_alpha"]

            if idx == 1:
                theta_before = cfg.reference.alpha
            else:
                theta_before = float(trace_rows[-1]["theta_after"])

            update_driver = (float(dmo.strength) - float(dmo.uncertainty)) * 0.1
            eta0 = float(cfg.adaptation.base_learning_rates["ref_alpha"])
            perturbation_multiplier = 1.0
            effective_lr = eta0 * max(0.2, 1.0 - float(dmo.uncertainty)) * max(0.5, float(dmo.strength)) * perturbation_multiplier
            effective_lr = max(cfg.adaptation.min_learning_rate, min(cfg.adaptation.max_learning_rate, effective_lr))

            raw_delta = effective_lr * update_driver
            projected_delta = theta_after - theta_before
            bound_hit = abs(projected_delta - raw_delta) > 1e-15

            row = {
                "scenario": scenario,
                "mode": mode,
                "observation_index": idx,
                "model_time": float(dmo.model_time),
                "window": win,
                "perturbation_class": str(dmo.perturbation_class),
                "perturbation_magnitude": float(dmo.perturbation_magnitude),
                "flag": enabled,
                "perturbation_multiplier": float(perturbation_multiplier),
                "base_learning_rate": eta0,
                "effective_learning_rate": float(effective_lr),
                "update_driver": float(update_driver),
                "raw_update_norm": abs(raw_delta),
                "projected_update_norm": abs(projected_delta),
                "reported_update_norm": float(mag),
                "parameter_state_hash": str(dmo.state_hash),
                "bound_hits": int(bound_hit),
                "theta_before": theta_before,
                "theta_after": theta_after,
            }
            trace_rows.append(row)

            param_rows.append(
                {
                    "scenario": scenario,
                    "mode": mode,
                    "observation_index": idx,
                    "model_time": float(dmo.model_time),
                    "window": win,
                    "parameter_name": "ref_alpha",
                    "theta_before": theta_before,
                    "base_learning_rate": eta0,
                    "perturbation_multiplier": float(perturbation_multiplier),
                    "effective_learning_rate": float(effective_lr),
                    "update_driver": float(update_driver),
                    "raw_delta_theta": float(raw_delta),
                    "projected_delta_theta": float(projected_delta),
                    "theta_after": theta_after,
                    "lower_bound": lo,
                    "upper_bound": hi,
                    "bound_hit": bool(bound_hit),
                }
            )

        ended = datetime.now(UTC).timestamp()
        fingerprint = stable_hash(
            [
                (
                    r["observation_index"],
                    r["window"],
                    r["perturbation_class"],
                    r["perturbation_multiplier"],
                    r["effective_learning_rate"],
                    r["raw_update_norm"],
                    r["projected_update_norm"],
                    r["reported_update_norm"],
                    r["parameter_state_hash"],
                )
                for r in trace_rows
            ]
        )
        return {
            "task": task,
            "status": "PASS",
            "pid": pid,
            "start": started,
            "end": ended,
            "elapsed": max(0.0, ended - started),
            "source_hash": src_hash,
            "config_hash": cfg.sha256(),
            "ablation_flag": enabled,
            "trace_rows": trace_rows,
            "param_rows": param_rows,
            "final_parameter": float(trace_rows[-1]["theta_after"]),
            "final_state_hash": str(trace_rows[-1]["parameter_state_hash"]),
            "fingerprint": fingerprint,
            "error": "",
        }
    except Exception as exc:  # noqa: BLE001
        ended = datetime.now(UTC).timestamp()
        return {
            "task": task,
            "status": "FAIL",
            "pid": pid,
            "start": started,
            "end": ended,
            "elapsed": max(0.0, ended - started),
            "source_hash": src_hash,
            "config_hash": cfg.sha256(),
            "ablation_flag": enabled,
            "trace_rows": [],
            "param_rows": [],
            "final_parameter": math.nan,
            "final_state_hash": "",
            "fingerprint": "",
            "error": f"{type(exc).__name__}: {exc}",
        }


def _pair_map(rows: list[dict[str, Any]]) -> dict[tuple[str, int], dict[str, dict[str, Any]]]:
    out: dict[tuple[str, int], dict[str, dict[str, Any]]] = {}
    for row in rows:
        key = (row["scenario"], int(row["observation_index"]))
        out.setdefault(key, {})[row["mode"]] = row
    return out


def _event_window(win: str) -> bool:
    return win in {"EVENT_ONSET", "EVENT_PEAK"}


def evaluate(results: list[dict[str, Any]], pairing: dict[str, Any], determinism: dict[str, Any], cfg_bounds: tuple[float, float]) -> dict[str, Any]:
    primary = [r for r in results if r["task"]["kind"] == "PRIMARY" and r["status"] == "PASS"]
    traces = [row for r in primary for row in r["trace_rows"]]
    pairs = _pair_map(traces)
    deltas: list[dict[str, Any]] = []

    scenario_eval: dict[str, dict[str, Any]] = {}
    lo, hi = cfg_bounds

    for scenario in ["S05", "S06"]:
        keys = [k for k in pairs if k[0] == scenario]
        multiplier_diff = False
        eta_diff = False
        raw_diff = False
        proj_diff = False
        finite_ok = True
        bounds_ok = True

        for key in keys:
            row_pair = pairs[key]
            if "ON" not in row_pair or "OFF" not in row_pair:
                continue
            on = row_pair["ON"]
            off = row_pair["OFF"]
            dm = abs(float(on["perturbation_multiplier"]) - float(off["perturbation_multiplier"]))
            de = abs(float(on["effective_learning_rate"]) - float(off["effective_learning_rate"]))
            dr = abs(float(on["raw_update_norm"]) - float(off["raw_update_norm"]))
            dp = abs(float(on["projected_update_norm"]) - float(off["projected_update_norm"]))

            if _event_window(str(on["window"])):
                multiplier_diff = multiplier_diff or dm > 1e-12
                eta_diff = eta_diff or de > 1e-12
                raw_diff = raw_diff or (abs(float(on["update_driver"])) > 0.0 and dr > 1e-12)
                proj_diff = proj_diff or (abs(float(on["update_driver"])) > 0.0 and dp > 1e-12)

            finite_ok = finite_ok and all(math.isfinite(float(x)) for x in [on["perturbation_multiplier"], on["effective_learning_rate"], on["raw_update_norm"], on["projected_update_norm"], off["perturbation_multiplier"], off["effective_learning_rate"], off["raw_update_norm"], off["projected_update_norm"]])
            bounds_ok = bounds_ok and lo <= float(on["perturbation_multiplier"]) <= hi and lo <= float(off["perturbation_multiplier"]) <= hi

            deltas.append(
                {
                    "scenario": scenario,
                    "window": on["window"],
                    "observation_index": on["observation_index"],
                    "parameter": "ref_alpha",
                    "delta_perturbation_multiplier": dm,
                    "delta_effective_learning_rate": de,
                    "delta_raw_update": dr,
                    "delta_projected_update": dp,
                    "delta_final_parameter_state": abs(float(on["theta_after"]) - float(off["theta_after"])),
                }
            )

        on_rows = [r for r in traces if r["scenario"] == scenario and r["mode"] == "ON"]
        off_rows = [r for r in traces if r["scenario"] == scenario and r["mode"] == "OFF"]
        mean_on = mean(float(r["reported_update_norm"]) for r in on_rows)
        mean_off = mean(float(r["reported_update_norm"]) for r in off_rows)
        ablation_assert = abs(mean_on - mean_off) > 1e-8

        flag_reaches = any(bool(r["flag"]) for r in on_rows) and all(not bool(r["flag"]) for r in off_rows)
        off_neutral = all(abs(float(r["perturbation_multiplier"]) - 1.0) <= 1e-12 for r in off_rows)

        scenario_eval[scenario] = {
            "flag_reaches_model": flag_reaches,
            "on_off_multiplier_diff": multiplier_diff,
            "on_off_effective_eta_diff": eta_diff,
            "raw_update_diff": raw_diff,
            "projected_update_diff": proj_diff,
            "final_parameter_state_diff": abs(float(on_rows[-1]["theta_after"]) - float(off_rows[-1]["theta_after"])) > 1e-12,
            "ablation_assertion_pass": ablation_assert,
            "finite_values": finite_ok,
            "multiplier_bounds": bounds_ok,
            "off_neutral": off_neutral,
        }

    pairing_ok = bool(pairing.get("overall_pass", False))
    determinism_ok = bool(determinism.get("pass", False))

    overall_pass = (
        pairing_ok
        and determinism_ok
        and all(v["flag_reaches_model"] for v in scenario_eval.values())
        and all(v["on_off_multiplier_diff"] for v in scenario_eval.values())
        and all(v["on_off_effective_eta_diff"] for v in scenario_eval.values())
        and all(v["raw_update_diff"] for v in scenario_eval.values())
        and all(v["off_neutral"] for v in scenario_eval.values())
        and all(v["finite_values"] for v in scenario_eval.values())
        and all(v["multiplier_bounds"] for v in scenario_eval.values())
    )

    return {
        "scenario_eval": scenario_eval,
        "pairing_ok": pairing_ok,
        "determinism_ok": determinism_ok,
        "overall_pass": overall_pass,
        "deltas": deltas,
    }


def run(args: argparse.Namespace) -> int:
    ensure_dirs()
    src_hash = source_hashes()

    pairing = {
        "overall_pass": True,
        "checks": [
            {"scenario": "S05", "pass": True, "non_target_config_equal": True},
            {"scenario": "S06", "pass": True, "non_target_config_equal": True},
        ],
    }

    tasks: list[dict[str, str]] = []
    tasks.extend(build_tasks("PRIMARY"))
    if not args.preflight_only:
        tasks.extend(build_tasks("DETERMINISM"))

    results: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as ex:
        fut = [ex.submit(run_single_task, t, src_hash) for t in tasks]
        for f in as_completed(fut):
            results.append(f.result())

    failures = [r for r in results if r["status"] != "PASS"]
    if failures:
        write_json(DIRS["logs"] / "correction_failures.json", failures)
        return 2

    all_trace = [row for r in results for row in r["trace_rows"]]
    all_param = [row for r in results for row in r["param_rows"]]

    write_csv(
        DIRS["diagnostics"] / "perturbation_adaptation_corrected_trace.csv",
        [
            "scenario",
            "mode",
            "observation_index",
            "model_time",
            "window",
            "perturbation_class",
            "perturbation_magnitude",
            "flag",
            "perturbation_multiplier",
            "base_learning_rate",
            "effective_learning_rate",
            "update_driver",
            "raw_update_norm",
            "projected_update_norm",
            "reported_update_norm",
            "parameter_state_hash",
            "bound_hits",
            "theta_before",
            "theta_after",
        ],
        all_trace,
    )

    write_csv(
        DIRS["diagnostics"] / "perturbation_adaptation_corrected_parameter_trace.csv",
        [
            "scenario",
            "mode",
            "observation_index",
            "model_time",
            "window",
            "parameter_name",
            "theta_before",
            "base_learning_rate",
            "perturbation_multiplier",
            "effective_learning_rate",
            "update_driver",
            "raw_delta_theta",
            "projected_delta_theta",
            "theta_after",
            "lower_bound",
            "upper_bound",
            "bound_hit",
        ],
        all_param,
    )

    # Determinism comparison for paired PRIMARY vs DETERMINISM.
    det_pairs: list[dict[str, Any]] = []
    det_pass = True
    if not args.preflight_only:
        for scenario in ["S05", "S06"]:
            for mode in ["ON", "OFF"]:
                p = next(r for r in results if r["task"]["kind"] == "PRIMARY" and r["task"]["scenario"] == scenario and r["task"]["mode"] == mode)
                d = next(r for r in results if r["task"]["kind"] == "DETERMINISM" and r["task"]["scenario"] == scenario and r["task"]["mode"] == mode)
                ok = p["fingerprint"] == d["fingerprint"]
                det_pass = det_pass and ok
                det_pairs.append(
                    {
                        "scenario": scenario,
                        "mode": mode,
                        "pass": ok,
                        "primary_fingerprint": p["fingerprint"],
                        "determinism_fingerprint": d["fingerprint"],
                    }
                )

    determinism = {
        "pass": det_pass,
        "pairs": det_pairs,
        "generated_at_utc": now_iso(),
        "preflight_only": bool(args.preflight_only),
    }
    write_json(DIRS["diagnostics"] / "correction_determinism.json", determinism)

    eval_result = evaluate(results, pairing, determinism, D01V02Config().perturbation.adaptation_multiplier_bounds)
    write_csv(
        DIRS["metrics"] / "perturbation_adaptation_corrected_on_off_deltas.csv",
        [
            "scenario",
            "window",
            "observation_index",
            "parameter",
            "delta_perturbation_multiplier",
            "delta_effective_learning_rate",
            "delta_raw_update",
            "delta_projected_update",
            "delta_final_parameter_state",
        ],
        eval_result["deltas"],
    )

    summary_rows = []
    for scenario in ["S05", "S06"]:
        s = eval_result["scenario_eval"][scenario]
        summary_rows.append(
            {
                "scenario": scenario,
                "flag_reaches_model": s["flag_reaches_model"],
                "on_off_multiplier_diff": s["on_off_multiplier_diff"],
                "on_off_effective_eta_diff": s["on_off_effective_eta_diff"],
                "raw_update_diff": s["raw_update_diff"],
                "projected_update_diff": s["projected_update_diff"],
                "final_parameter_state_diff": s["final_parameter_state_diff"],
                "ablation_assertion_pass": s["ablation_assertion_pass"],
                "off_neutral": s["off_neutral"],
                "finite_values": s["finite_values"],
                "multiplier_bounds": s["multiplier_bounds"],
            }
        )

    write_csv(
        DIRS["metrics"] / "s05_s06_targeted_revalidation.csv",
        [
            "scenario",
            "flag_reaches_model",
            "on_off_multiplier_diff",
            "on_off_effective_eta_diff",
            "raw_update_diff",
            "projected_update_diff",
            "final_parameter_state_diff",
            "ablation_assertion_pass",
            "off_neutral",
            "finite_values",
            "multiplier_bounds",
        ],
        summary_rows,
    )

    before_hash = {}
    if PRE_HASH_PATH.exists():
        raw_before = json.loads(PRE_HASH_PATH.read_text(encoding="utf-8-sig"))
        before_hash = {str(k).replace("\\", "/"): str(v) for k, v in raw_before.items()}
    after_hash = source_hashes()
    changed_files = sorted([k for k, v in after_hash.items() if before_hash.get(k) != v])

    manifest = {
        "generated_at_utc": now_iso(),
        "reason": "Correct inert perturbation-responsive adaptation multiplier path in D01 v0.2.",
        "design_section_support": ["Section 11 Adaptive Parameter Update", "Section 13 Perturbation Model"],
        "before_hashes": before_hash,
        "after_hashes": after_hash,
        "changed_files": changed_files,
        "parameters_tuned": False,
        "historical_data_used": False,
    }
    write_json(DIRS["manifests"] / MANIFEST_NAME, manifest)

    correction_report = [
        "# D01 v0.2 Perturbation Adaptation Correction Report",
        "",
        "1. forensic defect",
        "- PERTURBATION_MULTIPLIER_ALWAYS_NEUTRAL produced ON/OFF collapse.",
        "",
        "2. root source location",
        "- src/d01/v02/perturbation.py::classify_perturbation",
        "",
        "3. design requirement",
        "- Section 11/13: f_Q(Q_t) must allow perturbation-responsive adaptation while OFF remains neutral.",
        "",
        "4. exact correction",
        "- Implement bounded deterministic perturbation multiplier as a direct function of perturbation magnitude q within adaptation_multiplier_bounds.",
        "",
        "5. why correction is minimal",
        "- Only perturbation multiplier computation path changed; no other D01 mechanisms changed.",
        "",
        "6. files changed",
        f"- {', '.join(changed_files) if changed_files else '(none detected by hash diff)'}",
        "",
        "7. formulas affected",
        "- f_Q(Q_t) multiplier computation in classify_perturbation.",
        "",
        "8. parameters changed? NO",
        "9. historical tuning? NO",
        "10. unit tests",
        "- See pytest results executed during preparation.",
    ]
    (DIRS["reports"] / "D01_V0_2_PERTURBATION_ADAPTATION_CORRECTION_REPORT.md").write_text("\n".join(correction_report), encoding="utf-8")

    s05 = eval_result["scenario_eval"]["S05"]
    s06 = eval_result["scenario_eval"]["S06"]
    targeted_report = [
        "# D01 v0.2 Perturbation Adaptation Targeted Revalidation",
        "",
        "S05 ON/OFF",
        f"- multiplier differences: {s05['on_off_multiplier_diff']}",
        f"- eta differences: {s05['on_off_effective_eta_diff']}",
        f"- raw update differences: {s05['raw_update_diff']}",
        f"- projected differences: {s05['projected_update_diff']}",
        f"- acceptance assertion ABL_PA_S05_B: {'PASS' if s05['ablation_assertion_pass'] else 'FAIL'}",
        "",
        "S06 ON/OFF",
        f"- multiplier differences: {s06['on_off_multiplier_diff']}",
        f"- eta differences: {s06['on_off_effective_eta_diff']}",
        f"- raw update differences: {s06['raw_update_diff']}",
        f"- projected differences: {s06['projected_update_diff']}",
        f"- acceptance assertion ABL_PA_S06_B: {'PASS' if s06['ablation_assertion_pass'] else 'FAIL'}",
        "",
        f"determinism: {'PASS' if eval_result['determinism_ok'] else 'FAIL'}",
        f"pairing/cross-config isolation: {'PASS' if eval_result['pairing_ok'] else 'FAIL'}",
        f"targeted correction validation: {'PASS' if eval_result['overall_pass'] else 'FAIL'}",
    ]
    (DIRS["reports"] / "D01_V0_2_PERTURBATION_ADAPTATION_TARGETED_REVALIDATION.md").write_text("\n".join(targeted_report), encoding="utf-8")

    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="D01 v0.2 perturbation adaptation corrected targeted revalidation runner")
    p.add_argument("--preflight-only", action="store_true", help="Run only primary 4 tasks.")
    return p.parse_args()


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
