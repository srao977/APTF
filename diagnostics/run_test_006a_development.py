from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (
    ROOT,
    ROOT / "d01_adaptive_parametric_model" / "src",
    ROOT / "d02_return_shape" / "src",
    ROOT / "d04_trading_envelope" / "src",
    ROOT / "position_transition_controller",
):
    sys.path.insert(0, str(path))

from experimental_adaptive_emitter import AdaptiveEmitter, DevelopmentObservationStream


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    for item in manifest["frozen_rules_and_code"]:
        if sha256(ROOT / item["path"]) != item["sha256"]:
            raise RuntimeError(f"pre-execution hash drift: {item['path']}")

    emitter = AdaptiveEmitter(
        entity_id="SPY",
        rule_fingerprint=manifest["rule_fingerprint"],
        code_fingerprint=manifest["implementation_fingerprint"],
    )
    stream = DevelopmentObservationStream(
        ROOT / "data/market/normalized/SPY_1min_normalized_v0_1.csv",
        first_physical_row=115,
        last_physical_row=1114,
        reserve_start_utc="2023-03-30T08:00:00Z",
    )
    all_records = []
    try:
        while True:
            exposed = stream.next_observation()
            if exposed is None:
                break
            physical_row, source_row = exposed
            emission = emitter.process(physical_row, source_row)
            all_records.append(emission)
            if emission["status"] == "ACTIONABLE" and len(emitter.emissions) % 100 == 0:
                counts = Counter(item["position_decision"] for item in emitter.emissions)
                transitions = sum(left["position_decision"] != right["position_decision"] for left, right in zip(emitter.emissions, emitter.emissions[1:]))
                print(
                    f"TEST006A actionable={len(emitter.emissions)}/985 time={emission['observation_timestamp']} "
                    f"decision={emission['position_decision']} BUY={counts['BUY']} SELL={counts['SELL']} HOLD={counts['HOLD']} "
                    f"transitions={transitions} C={emission['mathematics']['C']} "
                    f"Q={emission['mathematics']['Q_G']}/{emission['mathematics']['Q_S']}/{emission['mathematics']['Q_R']} "
                    f"range_C={emission['adaptive_properties']['prior_15_range_C']} "
                    f"state={emission['state_after']} ns={emission['direct_lifecycle_ns']} future_access=0"
                )
    finally:
        stream.close()
    if len(all_records) != 1000 or len(emitter.initialization) != 15 or len(emitter.emissions) != 985:
        raise RuntimeError("development record count mismatch")
    if stream.reserve_rows_accessed != 0:
        raise RuntimeError("reserve access violation")
    payload = {
        "test_id": "APTF_TEST_006A_DEVELOPMENT_VALIDATION_V0_1",
        "manifest_sha256": sha256(args.manifest),
        "source_sha256": sha256(ROOT / "data/market/normalized/SPY_1min_normalized_v0_1.csv"),
        "development_range": [115, 1114],
        "reserve_start_utc": "2023-03-30T08:00:00Z",
        "reserve_rows_accessed": stream.reserve_rows_accessed,
        "rows_exposed": stream.rows_exposed,
        "initialization": emitter.initialization,
        "emissions": emitter.emissions,
        "adaptation_audit": emitter.adaptation_audit,
        "feedback_audit": emitter.feedback_audit,
        "all_record_hashes": [hashlib.sha256(json.dumps(item, sort_keys=True, separators=(",", ":")).encode()).hexdigest() for item in all_records],
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"initialization":15,"actionable":985,"reserve_accessed":0,"BUY":sum(x["position_decision"]=="BUY" for x in emitter.emissions),"SELL":sum(x["position_decision"]=="SELL" for x in emitter.emissions),"HOLD":sum(x["position_decision"]=="HOLD" for x in emitter.emissions)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())