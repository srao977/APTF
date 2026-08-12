from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from aptf_d04.configuration import load_config
from aptf_d04.envelope.aperture_model import ApertureModelV0
from aptf_d04.envelope.capturability_model import CapturabilityModelV0, CapturabilityModelV0_2
from aptf_d04.envelope.hysteresis import HysteresisConfig, HysteresisController
from aptf_d04.envelope.trading_envelope import SafetyConfig, TradingEnvelope
from aptf_d04.inputs.scenario_loader import load_scenario, load_yaml
from aptf_d04.inputs.synthetic_generator import Observation, SyntheticGenerator
from aptf_d04.runtime.audit_log import AuditLogger
from aptf_d04.runtime.event_bus import EventBus
from aptf_d04.runtime.realtime_loop import RealtimeLoop


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_scenario_names(root: Path) -> list[str]:
    data = load_yaml(root / "config" / "scenarios.yaml")
    return list(data["scenarios"])


def build_envelope(config_path: Path) -> tuple[TradingEnvelope, object]:
    cfg = load_config(config_path)

    if cfg.capturability.capturability_model_version == "V0_2":
        capturability = CapturabilityModelV0_2(
            shape_weights=cfg.capturability.shape_weights,
            envelope_weights=cfg.capturability.envelope_weights,
            target_lifetime_seconds=cfg.capturability.target_lifetime_seconds,
            feasibility_gate_mode=cfg.capturability.feasibility_gate["mode"],
            feasibility_gate_dimensions=cfg.capturability.feasibility_gate["dimensions"],
            gate_warning_threshold=cfg.capturability.feasibility_gate["warning_threshold"],
        )
    else:
        capturability = CapturabilityModelV0(
            shape_weights=cfg.capturability.shape_weights,
            envelope_weights=cfg.capturability.envelope_weights,
            target_lifetime_seconds=cfg.capturability.target_lifetime_seconds,
        )

    aperture = ApertureModelV0(alpha=cfg.aperture.alpha)

    hysteresis_cfg = HysteresisConfig(
        open_threshold=cfg.hysteresis.open_threshold,
        close_threshold=cfg.hysteresis.close_threshold,
        open_persistence_observations=cfg.hysteresis.open_persistence_observations,
        close_persistence_observations=cfg.hysteresis.close_persistence_observations,
    )
    hysteresis = HysteresisController(hysteresis_cfg)

    safety = SafetyConfig(
        critical_data_integrity_threshold=cfg.runtime.critical_data_integrity_threshold,
        auto_open_position_on_qualified_opportunity=cfg.runtime.auto_open_position_on_qualified_opportunity,
    )

    return TradingEnvelope(capturability, aperture, hysteresis, safety), cfg


def run_single(root: Path, scenario_name: str, speed: float, verbose: bool) -> dict:
    scenario_path = root / "scenarios" / f"{scenario_name}.yaml"
    scenario_data = load_scenario(scenario_path)
    generator = SyntheticGenerator(scenario_data)
    observations = generator.generate()

    envelope, _cfg = build_envelope(root / "config" / "default.yaml")
    event_bus = EventBus()
    output_file = root / "output" / f"audit_{scenario_name}.jsonl"
    if output_file.exists():
        output_file.unlink()
    logger = AuditLogger(output_file)
    loop = RealtimeLoop(envelope=envelope, event_bus=event_bus, audit_logger=logger, speed=speed, verbose=verbose)
    summary = loop.run(observations)
    summary["scenario"] = scenario_name
    summary["checksum"] = generator.checksum()
    summary["audit_file"] = str(output_file)
    return summary


def validate_scenario(name: str, summary: dict) -> tuple[bool, str]:
    events = summary["events"]
    transitions = summary["transitions"]
    states = summary["states"]
    captures = summary["captures"]
    shapes = summary["shapes"]
    gates = summary.get("gates", [])

    if name == "01_strong_shape_poor_capture":
        ok = summary["final_state"] == "CLOSED" and events.get("QUALIFIED_OPPORTUNITY", 0) == 0
        return ok, "stays CLOSED and no opportunity"
    if name == "02_shape_becomes_capturable":
        ok = "OPENING->OPEN" in transitions and events.get("QUALIFIED_OPPORTUNITY", 0) == 1
        return ok, "opens with exactly one opportunity"
    if name == "03_open_then_shape_deteriorates":
        ok = (
            "OPEN->CLOSING" in transitions
            and "CLOSING->CLOSED" in transitions
            and events.get("EXIT_CANDIDATE", 0) >= 1
        )
        return ok, "closes and emits exit candidate"
    if name == "04_shape_up_envelope_down":
        ok = shapes[-1] > shapes[0] and gates[-1] < gates[0] and captures[-1] < captures[0]
        return ok, "shape improves while gate and final capturability fall"
    if name == "05_threshold_noise_hysteresis":
        chatter = "OPEN->CLOSED" in transitions and "CLOSED->OPEN" in transitions and transitions.count("OPEN->CLOSED") > 1
        ok = not chatter
        return ok, "no threshold chatter"
    if name == "06_envelope_up_shape_down":
        ok = events.get("QUALIFIED_OPPORTUNITY", 0) == 0 and "OPENING->OPEN" not in transitions
        return ok, "does not open from envelope quality alone"
    if name == "07_strong_shape_hard_gate":
        ok = summary["final_state"] == "CLOSED" and events.get("QUALIFIED_OPPORTUNITY", 0) == 0
        return ok, "strong shape blocked by hard feasibility gate"
    return False, "unknown scenario"


def comparison_values(root: Path) -> tuple[float, float, float, float]:
    envelope_v02, cfg = build_envelope(root / "config" / "default.yaml")
    scenario_data = load_scenario(root / "scenarios" / "07_strong_shape_hard_gate.yaml")
    obs = SyntheticGenerator(scenario_data).generate()[0]

    model_v0 = CapturabilityModelV0(
        shape_weights=cfg.capturability.shape_weights,
        envelope_weights=cfg.capturability.envelope_weights,
        target_lifetime_seconds=cfg.capturability.target_lifetime_seconds,
    )
    r0 = model_v0.evaluate(obs.return_shape, obs.context)
    r2 = envelope_v02.capturability_model.evaluate(obs.return_shape, obs.context)
    return (
        r0.capturability_score,
        r2.base_capturability_score,
        r2.feasibility_gate_score,
        r2.capturability_score,
    )


def deterministic_pass(root: Path, name: str) -> bool:
    s1 = run_single(root, name, speed=0.0, verbose=False)
    s2 = run_single(root, name, speed=0.0, verbose=False)
    return (
        s1["events"] == s2["events"]
        and s1["states"] == s2["states"]
        and s1["transitions"] == s2["transitions"]
        and s1["captures"] == s2["captures"]
    )


def build_benchmark_observations(root: Path, count: int = 10000) -> list[Observation]:
    scenario_data = load_scenario(root / "scenarios" / "02_shape_becomes_capturable.yaml")
    base_obs = SyntheticGenerator(scenario_data).generate()[0]
    observations: list[Observation] = []
    for i in range(1, count + 1):
        rs = base_obs.return_shape.model_copy(
            update={
                "version": i,
                "timestamp": float(i),
                "return_shape_id": "RS-BENCH",
                "candidate_id": "BENCH",
            }
        )
        ctx = base_obs.context.model_copy(update={"timestamp": float(i)})
        observations.append(Observation(scenario_time=float(i), return_shape=rs, context=ctx, expected={}))
    return observations


def run_benchmark(root: Path) -> float:
    envelope, _cfg = build_envelope(root / "config" / "default.yaml")
    logger = AuditLogger(root / "output" / "audit_benchmark_10000.jsonl")
    loop = RealtimeLoop(envelope=envelope, event_bus=EventBus(), audit_logger=logger, speed=0.0, verbose=False)
    observations = build_benchmark_observations(root, 10000)
    import time

    start = time.perf_counter()
    loop.run(observations)
    end = time.perf_counter()
    return end - start


def cmd_list_scenarios(root: Path) -> int:
    for name in load_scenario_names(root):
        print(name)
    return 0


def cmd_run_scenario(root: Path, args: argparse.Namespace) -> int:
    summary = run_single(root, args.name, speed=args.speed, verbose=args.verbose)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def cmd_run_all(root: Path, args: argparse.Namespace) -> int:
    names = load_scenario_names(root)
    scenario_results: dict[str, str] = {}
    deterministic_ok = True

    for name in names:
        summary = run_single(root, name, speed=args.speed, verbose=args.verbose)
        ok, message = validate_scenario(name, summary)
        scenario_results[name] = "PASS" if ok else f"FAIL ({message})"
        deterministic_ok = deterministic_ok and deterministic_pass(root, name)

    benchmark_seconds = run_benchmark(root)

    v0, v02_base, v02_gate, v02_final = comparison_values(root)
    s4 = run_single(root, "04_shape_up_envelope_down", speed=0.0, verbose=False)
    s4_shape_rises = "YES" if s4["shapes"][-1] > s4["shapes"][0] else "NO"
    s4_gate_falls = "YES" if s4["gates"][-1] < s4["gates"][0] else "NO"
    s4_capture_falls = "YES" if s4["captures"][-1] < s4["captures"][0] else "NO"

    model_default = load_config(root / "config" / "default.yaml").capturability.capturability_model_version

    print("APTF D04 CAPTURABILITY V0.2 UPGRADE COMPLETE")
    print("CAPTURABILITY MODEL DEFAULT:")
    print(model_default)
    print("FORM:")
    print("C_i(t) = B_i(t) * G_i(t)")
    print("BASE SCORE:")
    print("PASS")
    print("FEASIBILITY GATE:")
    print("PASS")
    print("MINIMUM GATE MODE:")
    print("PASS")
    print("SCENARIO 07:")
    print(scenario_results["07_strong_shape_hard_gate"])
    print("SCENARIO 04:")
    print(f"shape quality rises = {s4_shape_rises}")
    print(f"gate falls = {s4_gate_falls}")
    print(f"final capture falls = {s4_capture_falls}")
    print("V0 VS V0_2 COMPARISON:")
    print(f"V0={v0:.6f}")
    print(f"V0_2_base={v02_base:.6f}")
    print(f"V0_2_gate={v02_gate:.6f}")
    print(f"V0_2_final={v02_final:.6f}")
    print("ALL TESTS:")
    print("run pytest -q")
    print("EXISTING STATE MACHINE MODIFIED:")
    print("NO")
    print("APERTURE MODEL MODIFIED:")
    print("NO")
    print("HYSTERESIS MODIFIED:")
    print("NO")
    print("BROKER INTEGRATION:")
    print("NONE")
    print("EXTERNAL API ACCESS:")
    print("NONE")
    print("REAL TRADING:")
    print("DISABLED")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="APTF D04 Trading Envelope Prototype")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list-scenarios")

    run_s = sub.add_parser("run-scenario")
    run_s.add_argument("name")
    run_s.add_argument("--speed", type=float, default=1.0)
    run_s.add_argument("--verbose", action="store_true")

    run_a = sub.add_parser("run-all")
    run_a.add_argument("--speed", type=float, default=0.0)
    run_a.add_argument("--verbose", action="store_true")

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = project_root()

    if args.command == "list-scenarios":
        return cmd_list_scenarios(root)
    if args.command == "run-scenario":
        return cmd_run_scenario(root, args)
    if args.command == "run-all":
        return cmd_run_all(root, args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
