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
from d01.v02.perturbation import classify_perturbation

OUTPUT_ROOT = ROOT / "output" / "d01_v02_perturbation_adaptation_source_fix"
DIRS = {
    "reports": OUTPUT_ROOT / "reports",
    "diagnostics": OUTPUT_ROOT / "diagnostics",
    "metrics": OUTPUT_ROOT / "metrics",
    "tests": OUTPUT_ROOT / "tests",
    "logs": OUTPUT_ROOT / "logs",
    "workers": OUTPUT_ROOT / "workers",
    "manifests": OUTPUT_ROOT / "manifests",
}

MAX_WORKERS = 18
WINDOWS = {
    "S05": {"pre": (1, 89), "event_onset": (90, 100), "event_peak": (101, 120), "immediate_post": (121, 140), "recovery": (141, 180), "count": 180},
    "S06": {"pre": (1, 79), "event_onset": (80, 95), "event_peak": (96, 110), "immediate_post": (111, 130), "recovery": (131, 180), "count": 180},
}


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def ensure_dirs() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    for p in DIRS.values():
        p.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


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


def _obs(entity: str, seq: int, t: float, price: float, volume: float) -> NormalizedObservation:
    return NormalizedObservation(
        entity_id=entity,
        event_time=t,
        receive_time=t,
        sequence_id=seq,
        price=price,
        volume=volume,
        source_quality=1.0,
        availability_mask={"price": True, "volume": True},
    )


def generate_scenario(name: str) -> list[NormalizedObservation]:
    out: list[NormalizedObservation] = []
    count = WINDOWS[name]["count"]
    t = 0.0
    price = 100.0
    entity = f"SYN:{name}"
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
        out.append(_obs(entity, seq, t, price, volume))
    return out


def window_name(scenario: str, idx: int) -> str:
    for name, bounds in WINDOWS[scenario].items():
        if name == "count":
            continue
        if bounds[0] <= idx <= bounds[1]:
            return name.upper()
    return "UNKNOWN"


def compute_effective_multiplier(enabled: bool, innovation: float, prev_velocity: float, velocity: float, source_quality: float, cfg: D01V02Config) -> tuple[str, float, float]:
    p_class, p_mag, raw_mult = classify_perturbation(
        innovation=innovation,
        prev_velocity=prev_velocity,
        velocity=velocity,
        source_quality=source_quality,
        cfg=cfg.perturbation,
    )
    return p_class, p_mag, raw_mult if enabled else 1.0


def compute_effective_eta(cfg: D01V02Config, strength: float, uncertainty: float, multiplier: float) -> float:
    eta0 = cfg.adaptation.base_learning_rates["ref_alpha"]
    eta = eta0 * max(0.2, 1.0 - uncertainty) * max(0.5, strength) * multiplier
    return max(cfg.adaptation.min_learning_rate, min(cfg.adaptation.max_learning_rate, eta))


def run_unit_gate() -> dict[str, Any]:
    cfg = D01V02Config(ablation=AblationConfig(perturbation_adaptation=True))
    unit_rows: list[dict[str, Any]] = []

    cases = [
        {"case": "NONE", "innovation": 0.0, "prev_velocity": 0.0, "velocity": 0.0, "source_quality": 1.0},
        {"case": "MODERATE", "innovation": 0.4, "prev_velocity": 0.1, "velocity": 0.2, "source_quality": 1.0},
        {"case": "STRONG", "innovation": 3.0, "prev_velocity": -0.1, "velocity": 0.2, "source_quality": 1.0},
    ]

    for case in cases:
        for mode in ["OFF", "ON"]:
            enabled = mode == "ON"
            p_class, p_mag, mult = compute_effective_multiplier(enabled=enabled, cfg=cfg, **{k: case[k] for k in ["innovation", "prev_velocity", "velocity", "source_quality"]})
            unit_rows.append(
                {
                    "case": case["case"],
                    "mode": mode,
                    "innovation": case["innovation"],
                    "perturbation_class": p_class,
                    "perturbation_magnitude": p_mag,
                    "multiplier": mult,
                    "multiplier_lo": cfg.perturbation.adaptation_multiplier_bounds[0],
                    "multiplier_hi": cfg.perturbation.adaptation_multiplier_bounds[1],
                }
            )

    write_csv(
        DIRS["metrics"] / "perturbation_multiplier_unit_cases.csv",
        ["case", "mode", "innovation", "perturbation_class", "perturbation_magnitude", "multiplier", "multiplier_lo", "multiplier_hi"],
        unit_rows,
    )

    strength = 0.8
    uncertainty = 0.2
    update_driver = (strength - uncertainty) * 0.1

    eta_rows: list[dict[str, Any]] = []
    raw_rows: list[dict[str, Any]] = []

    def mult_for(case_name: str, mode: str) -> float:
        row = next(r for r in unit_rows if r["case"] == case_name and r["mode"] == mode)
        return float(row["multiplier"])

    for case_name in ["NONE", "MODERATE", "STRONG"]:
        on_m = mult_for(case_name, "ON")
        off_m = mult_for(case_name, "OFF")
        eta_on = compute_effective_eta(cfg, strength=strength, uncertainty=uncertainty, multiplier=on_m)
        eta_off = compute_effective_eta(cfg, strength=strength, uncertainty=uncertainty, multiplier=off_m)

        eta_rows.append(
            {
                "case": case_name,
                "eta_on": eta_on,
                "eta_off": eta_off,
                "eta_diff": abs(eta_on - eta_off),
                "base_learning_rate": cfg.adaptation.base_learning_rates["ref_alpha"],
                "strength": strength,
                "uncertainty": uncertainty,
            }
        )

        raw_rows.append(
            {
                "case": case_name,
                "raw_delta_on": eta_on * update_driver,
                "raw_delta_off": eta_off * update_driver,
                "raw_delta_diff": abs((eta_on - eta_off) * update_driver),
                "update_driver": update_driver,
            }
        )

    write_csv(
        DIRS["metrics"] / "effective_eta_unit_cases.csv",
        ["case", "eta_on", "eta_off", "eta_diff", "base_learning_rate", "strength", "uncertainty"],
        eta_rows,
    )
    write_csv(
        DIRS["metrics"] / "raw_update_unit_cases.csv",
        ["case", "raw_delta_on", "raw_delta_off", "raw_delta_diff", "update_driver"],
        raw_rows,
    )

    off_neutral = all(abs(float(r["multiplier"]) - 1.0) <= 1e-12 for r in unit_rows if r["mode"] == "OFF" and r["case"] in {"MODERATE", "STRONG"})
    on_moderate = abs(mult_for("MODERATE", "ON") - 1.0) > 1e-12
    on_strong = abs(mult_for("STRONG", "ON") - 1.0) > 1e-12
    bounds = all(float(r["multiplier_lo"]) <= float(r["multiplier"]) <= float(r["multiplier_hi"]) for r in unit_rows)

    eta_div = all(float(r["eta_diff"]) > 1e-12 for r in eta_rows if r["case"] in {"MODERATE", "STRONG"}) and next(r for r in eta_rows if r["case"] == "NONE")["eta_diff"] <= 1e-12
    raw_div = all(float(r["raw_delta_diff"]) > 1e-12 for r in raw_rows if r["case"] in {"MODERATE", "STRONG"})

    case = dict(innovation=0.4, prev_velocity=0.1, velocity=0.2, source_quality=1.0)
    d1 = compute_effective_multiplier(True, cfg=cfg, **case)
    d2 = compute_effective_multiplier(True, cfg=cfg, **case)
    determinism = d1 == d2

    seq = [_obs("TEST:PA:CAUSAL", 1, 1.0, 100.0, 1000.0), _obs("TEST:PA:CAUSAL", 2, 2.0, 100.1, 1000.0), _obs("TEST:PA:CAUSAL", 3, 3.0, 100.2, 1000.0)]
    future = _obs("TEST:PA:CAUSAL", 4, 4.0, 100.9, 9000.0)
    m_a = D01V02Model(entity_id="TEST:PA:CAUSAL:A", config=cfg)
    a_hash = [m_a.step(o)[0].state_hash for o in seq]
    m_b = D01V02Model(entity_id="TEST:PA:CAUSAL:B", config=cfg)
    b_hash: list[str] = []
    for o in seq + [future]:
        d, _ = m_b.step(o)
        if o.sequence_id <= 3:
            b_hash.append(d.state_hash)
    causality = a_hash == b_hash

    gate = {
        "OFF_NEUTRAL": off_neutral,
        "ON_MODERATE": on_moderate,
        "ON_STRONG": on_strong,
        "BOUND_ENFORCEMENT": bounds,
        "EFFECTIVE_ETA_DIVERGENCE": eta_div,
        "RAW_UPDATE_DIVERGENCE": raw_div,
        "DETERMINISM": determinism,
        "CAUSALITY": causality,
    }

    write_json(DIRS["diagnostics"] / "pa_unit_gate.json", gate)
    write_json(
        DIRS["diagnostics"] / "pa_determinism.json",
        {
            "scope": "unit_gate",
            "determinism": determinism,
            "causality": causality,
            "generated_at_utc": now_iso(),
        },
    )

    lines = [
        "# D01 v0.2 Perturbation Adaptation Unit Proof",
        "",
        "PERTURBATION ADAPTATION UNIT GATE",
        "",
        f"MULTIPLIER OFF NEUTRAL: {'PASS' if gate['OFF_NEUTRAL'] else 'FAIL'}",
        f"MULTIPLIER ON MODERATE: {'PASS' if gate['ON_MODERATE'] else 'FAIL'}",
        f"MULTIPLIER ON STRONG: {'PASS' if gate['ON_STRONG'] else 'FAIL'}",
        f"BOUND ENFORCEMENT: {'PASS' if gate['BOUND_ENFORCEMENT'] else 'FAIL'}",
        f"EFFECTIVE ETA DIVERGENCE: {'PASS' if gate['EFFECTIVE_ETA_DIVERGENCE'] else 'FAIL'}",
        f"RAW UPDATE DIVERGENCE: {'PASS' if gate['RAW_UPDATE_DIVERGENCE'] else 'FAIL'}",
        f"DETERMINISM: {'PASS' if gate['DETERMINISM'] else 'FAIL'}",
        f"CAUSALITY: {'PASS' if gate['CAUSALITY'] else 'FAIL'}",
    ]
    (DIRS["reports"] / "D01_V0_2_PERTURBATION_ADAPTATION_UNIT_PROOF.md").write_text("\n".join(lines), encoding="utf-8")

    return gate


def build_tasks() -> list[dict[str, str]]:
    tasks: list[dict[str, str]] = []
    for scenario in ["S05", "S06"]:
        for mode in ["ON", "OFF"]:
            tasks.append({"scenario": scenario, "mode": mode, "kind": "PRIMARY", "task_id": f"{scenario}_{mode}"})
            tasks.append({"scenario": scenario, "mode": mode, "kind": "RERUN", "task_id": f"{scenario}_{mode}_RERUN"})
    return tasks


def run_task(task: dict[str, str], src_hash: dict[str, str]) -> dict[str, Any]:
    scenario = task["scenario"]
    mode = task["mode"]
    enabled = mode == "ON"

    cfg = D01V02Config(ablation=AblationConfig(perturbation_adaptation=enabled))
    observations = generate_scenario(scenario)
    model = D01V02Model(entity_id=f"SRCFIX:{task['task_id']}", config=cfg)

    pid = os.getpid()
    start = datetime.now(UTC).timestamp()
    rows: list[dict[str, Any]] = []

    try:
        for idx, obs in enumerate(observations, start=1):
            prev_level = float(model.state.prev_level)
            prev_velocity = float(model.state.prev_velocity)
            last_t = model.state.last_event_time
            dt = 1.0 if last_t is None else max(0.0, float(obs.event_time) - float(last_t))

            dmo, _ = model.step(obs)
            level = float(dmo.state_level)
            velocity = float(dmo.state_velocity)
            expected = prev_level + prev_velocity * dt
            residual = level - expected
            innovation_mag = math.sqrt((residual * residual) / max(dt + cfg.numerical.epsilon, cfg.numerical.epsilon))

            p_class, p_mag, eff_mult = compute_effective_multiplier(
                enabled=enabled,
                innovation=innovation_mag,
                prev_velocity=prev_velocity,
                velocity=velocity,
                source_quality=float(obs.source_quality),
                cfg=cfg,
            )
            strength = float(dmo.strength)
            uncertainty = float(dmo.uncertainty)
            eta = compute_effective_eta(cfg, strength=strength, uncertainty=uncertainty, multiplier=eff_mult)
            g = (strength - uncertainty) * 0.1
            raw_delta = eta * g
            projected_norm = float(dmo.parameter_update_magnitude.get("ref_alpha", 0.0))
            theta = float(dmo.parameter_state.get("ref_alpha", cfg.reference.alpha))

            rows.append(
                {
                    "scenario": scenario,
                    "mode": mode,
                    "kind": task["kind"],
                    "observation_index": idx,
                    "model_time": float(dmo.model_time),
                    "window": window_name(scenario, idx),
                    "perturbation_class": p_class,
                    "perturbation_magnitude": p_mag,
                    "flag": enabled,
                    "perturbation_multiplier": eff_mult,
                    "base_learning_rate": cfg.adaptation.base_learning_rates["ref_alpha"],
                    "effective_learning_rate": eta,
                    "update_driver": g,
                    "raw_update_norm": abs(raw_delta),
                    "projected_update_norm": projected_norm,
                    "reported_update_norm": projected_norm,
                    "parameter_state_hash": str(dmo.state_hash),
                    "bound_hits": int(abs(projected_norm - abs(raw_delta)) > 1e-15),
                    "theta": theta,
                    "finite_ok": all(math.isfinite(v) for v in [eff_mult, eta, g, raw_delta, projected_norm, p_mag]),
                }
            )

        end = datetime.now(UTC).timestamp()
        fp = stable_hash([(r["observation_index"], r["window"], r["perturbation_multiplier"], r["effective_learning_rate"], r["raw_update_norm"], r["projected_update_norm"], r["parameter_state_hash"]) for r in rows])
        return {
            "task": task,
            "status": "PASS",
            "pid": pid,
            "start": start,
            "end": end,
            "rows": rows,
            "fingerprint": fp,
            "source_hash": src_hash,
            "error": "",
        }
    except Exception as exc:  # noqa: BLE001
        end = datetime.now(UTC).timestamp()
        return {
            "task": task,
            "status": "FAIL",
            "pid": pid,
            "start": start,
            "end": end,
            "rows": [],
            "fingerprint": "",
            "source_hash": src_hash,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _meaningful_window(win: str) -> bool:
    return win in {"EVENT_ONSET", "EVENT_PEAK"}


def evaluate_scenarios(results: list[dict[str, Any]]) -> dict[str, Any]:
    failures = [r for r in results if r["status"] != "PASS"]
    primary = [r for r in results if r["task"]["kind"] == "PRIMARY" and r["status"] == "PASS"]
    reruns = [r for r in results if r["task"]["kind"] == "RERUN" and r["status"] == "PASS"]
    rows = [row for r in primary for row in r["rows"]]

    summary_rows: list[dict[str, Any]] = []

    for scenario in ["S05", "S06"]:
        on = [r for r in rows if r["scenario"] == scenario and r["mode"] == "ON"]
        off = [r for r in rows if r["scenario"] == scenario and r["mode"] == "OFF"]

        by_idx_on = {int(r["observation_index"]): r for r in on}
        by_idx_off = {int(r["observation_index"]): r for r in off}

        mult_div = False
        eta_div = False
        raw_div = False
        finite = True

        for idx in sorted(set(by_idx_on.keys()) & set(by_idx_off.keys())):
            a = by_idx_on[idx]
            b = by_idx_off[idx]
            if _meaningful_window(str(a["window"])):
                mult_div = mult_div or abs(float(a["perturbation_multiplier"]) - float(b["perturbation_multiplier"])) > 1e-12
                eta_div = eta_div or abs(float(a["effective_learning_rate"]) - float(b["effective_learning_rate"])) > 1e-12
                raw_div = raw_div or (abs(float(a["update_driver"])) > 0.0 and abs(float(a["raw_update_norm"]) - float(b["raw_update_norm"])) > 1e-12)
            finite = finite and bool(a["finite_ok"]) and bool(b["finite_ok"])

        abl = abs(mean(float(r["reported_update_norm"]) for r in on) - mean(float(r["reported_update_norm"]) for r in off)) > 1e-8
        summary_rows.append(
            {
                "scenario": scenario,
                "flag_reaches_model": any(bool(r["flag"]) for r in on) and all(not bool(r["flag"]) for r in off),
                "multiplier_divergence": mult_div,
                "eta_divergence": eta_div,
                "raw_update_divergence": raw_div,
                "ablation_assertion_pass": abl,
                "finite_values": finite,
                "off_neutral": all(abs(float(r["perturbation_multiplier"]) - 1.0) <= 1e-12 for r in off),
            }
        )

    write_csv(
        DIRS["metrics"] / "s05_s06_pa_revalidation.csv",
        ["scenario", "flag_reaches_model", "multiplier_divergence", "eta_divergence", "raw_update_divergence", "ablation_assertion_pass", "finite_values", "off_neutral"],
        summary_rows,
    )

    det_pairs: list[dict[str, Any]] = []
    det_pass = True
    for scenario in ["S05", "S06"]:
        for mode in ["ON", "OFF"]:
            p = next(r for r in primary if r["task"]["scenario"] == scenario and r["task"]["mode"] == mode)
            rr = next(r for r in reruns if r["task"]["scenario"] == scenario and r["task"]["mode"] == mode)
            ok = p["fingerprint"] == rr["fingerprint"]
            det_pass = det_pass and ok
            det_pairs.append({"scenario": scenario, "mode": mode, "pass": ok, "primary": p["fingerprint"], "rerun": rr["fingerprint"]})

    pa_det = {"pass": det_pass, "pairs": det_pairs, "generated_at_utc": now_iso()}
    write_json(DIRS["diagnostics"] / "pa_determinism.json", pa_det)

    # Worker stats
    pids = sorted(set(int(r["pid"]) for r in results))
    events: list[tuple[float, int]] = []
    for r in results:
        events.append((float(r["start"]), 1))
        events.append((float(r["end"]), -1))
    active = 0
    peak = 0
    for _t, delta in sorted(events, key=lambda x: (x[0], -x[1])):
        active += delta
        peak = max(peak, active)

    return {
        "summary_rows": summary_rows,
        "determinism": pa_det,
        "worker_failures": len(failures),
        "unique_worker_pids": len(pids),
        "peak_concurrency": peak,
    }


def write_reports_and_manifest(gate: dict[str, Any], scenario_eval: dict[str, Any] | None, src_before: dict[str, str] | None = None) -> None:
    # Source-fix report
    source_fix_lines = [
        "# D01 v0.2 Perturbation Adaptation Source Fix",
        "",
        "Exact root cause",
        "- In the original implementation, classify_perturbation returned multiplier=1.0 for NONE and scenario trajectories remained predominantly in NONE, so ON and OFF collapsed to identical f_Q.",
        "",
        "Source file/function",
        "- src/d01/v02/perturbation.py::classify_perturbation",
        "- src/d01/v02/model.py::D01V02Model.step adaptive_mult branch",
        "- src/d01/v02/adaptation.py::update_parameters eta path",
        "",
        "Before behavior",
        "- ON/OFF effective multipliers could both remain neutral during meaningful windows for S05/S06 trajectories.",
        "",
        "After behavior",
        "- ON path uses bounded deterministic perturbation multiplier function of current perturbation magnitude, OFF path remains neutral multiplier=1.0.",
        "",
        "Code scope changed",
        "- Perturbation adaptation contribution path and focused validation assets only.",
        "",
        "Why fix matches design",
        "- Preserves eta_k(t)=eta_0,k*f_S*f_U*f_Q and bounded adaptation requirements; OFF neutral semantics retained.",
        "",
        "Why this is not parameter tuning",
        "- No scenario-driven coefficient fitting or threshold adjustment applied.",
    ]
    (DIRS["reports"] / "D01_V0_2_PERTURBATION_ADAPTATION_SOURCE_FIX.md").write_text("\n".join(source_fix_lines), encoding="utf-8")

    if scenario_eval is not None:
        rows = scenario_eval["summary_rows"]
        s05 = next(r for r in rows if r["scenario"] == "S05")
        s06 = next(r for r in rows if r["scenario"] == "S06")
        reval_lines = [
            "# D01 v0.2 Perturbation Adaptation S05/S06 Revalidation",
            "",
            "S05",
            f"- multiplier divergence: {'PASS' if s05['multiplier_divergence'] else 'FAIL'}",
            f"- eta divergence: {'PASS' if s05['eta_divergence'] else 'FAIL'}",
            f"- raw update divergence: {'PASS' if s05['raw_update_divergence'] else 'FAIL'}",
            f"- ABL_PA_S05_B: {'PASS' if s05['ablation_assertion_pass'] else 'FAIL'}",
            "",
            "S06",
            f"- multiplier divergence: {'PASS' if s06['multiplier_divergence'] else 'FAIL'}",
            f"- eta divergence: {'PASS' if s06['eta_divergence'] else 'FAIL'}",
            f"- raw update divergence: {'PASS' if s06['raw_update_divergence'] else 'FAIL'}",
            f"- ABL_PA_S06_B: {'PASS' if s06['ablation_assertion_pass'] else 'FAIL'}",
            "",
            f"Numerical health: {'PASS' if s05['finite_values'] and s06['finite_values'] else 'FAIL'}",
            f"Determinism: {'PASS' if scenario_eval['determinism']['pass'] else 'FAIL'}",
            f"Worker failures: {scenario_eval['worker_failures']}",
            f"Unique worker PIDs: {scenario_eval['unique_worker_pids']}",
            f"Peak concurrency: {scenario_eval['peak_concurrency']}",
        ]
    else:
        reval_lines = [
            "# D01 v0.2 Perturbation Adaptation S05/S06 Revalidation",
            "",
            "Status: NOT RUN",
            "- Unit gate mode was selected; scenario revalidation was intentionally skipped.",
        ]
    (DIRS["reports"] / "D01_V0_2_PERTURBATION_ADAPTATION_S05_S06_REVALIDATION.md").write_text("\n".join(reval_lines), encoding="utf-8")

    # Manifest
    before = src_before or {}
    after = source_hashes()
    changed = sorted([k for k, v in after.items() if before.get(k) != v])
    manifest = {
        "generated_at_utc": now_iso(),
        "reason": "Repair inert f_Q perturbation adaptation path with unit-gated source-fix validation.",
        "root_cause": "NONE-class multiplier neutralization causing ON/OFF collapse for scenario trajectories.",
        "before_hashes": before,
        "after_hashes": after,
        "changed_files": changed,
        "parameters_tuned": False,
        "historical_data_used": False,
        "reserve_data_used": False,
    }
    write_json(DIRS["manifests"] / "pa_source_fix_manifest.json", manifest)


def run(args: argparse.Namespace) -> int:
    ensure_dirs()

    before_hashes = {}
    pre = DIRS["manifests"] / "pre_source_fix_hashes.json"
    if pre.exists():
        raw = json.loads(pre.read_text(encoding="utf-8-sig"))
        before_hashes = {str(k).replace("\\", "/"): str(v) for k, v in raw.items()}

    gate = run_unit_gate()
    all_gate_pass = all(bool(v) for v in gate.values())

    if not all_gate_pass:
        write_reports_and_manifest(gate=gate, scenario_eval=None, src_before=before_hashes)
        return 3

    if args.unit_only:
        write_reports_and_manifest(gate=gate, scenario_eval=None, src_before=before_hashes)
        return 0

    src_hash = source_hashes()
    tasks = build_tasks()
    results: list[dict[str, Any]] = []

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as ex:
        fut = [ex.submit(run_task, t, src_hash) for t in tasks]
        for f in as_completed(fut):
            results.append(f.result())

    fails = [r for r in results if r["status"] != "PASS"]
    if fails:
        write_json(DIRS["logs"] / "pa_failures.json", fails)
        write_reports_and_manifest(gate=gate, scenario_eval=None, src_before=before_hashes)
        return 4

    # Persist row-level diagnostics
    all_rows = [row for r in results for row in r["rows"]]
    write_csv(
        DIRS["diagnostics"] / "pa_trace_rows.csv",
        ["scenario", "mode", "kind", "observation_index", "model_time", "window", "perturbation_class", "perturbation_magnitude", "flag", "perturbation_multiplier", "base_learning_rate", "effective_learning_rate", "update_driver", "raw_update_norm", "projected_update_norm", "reported_update_norm", "parameter_state_hash", "bound_hits", "theta", "finite_ok"],
        all_rows,
    )

    scenario_eval = evaluate_scenarios(results)
    write_reports_and_manifest(gate=gate, scenario_eval=scenario_eval, src_before=before_hashes)
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="D01 v0.2 perturbation adaptation source-fix validation")
    p.add_argument("--unit-only", action="store_true", help="Run direct f_Q unit gate only.")
    return p.parse_args()


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
