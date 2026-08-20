from __future__ import annotations

import json

from run_test_014c_validation import ROOT, build_acceptance_gates, sha256, write_json


def main() -> int:
    summary_path = ROOT / "APTF_TEST_014C_SUMMARY_V0_1.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    gates = build_acceptance_gates(summary)
    if gates["passed"] != gates["required"]:
        raise RuntimeError(f'{gates["passed"]}/{gates["required"]} acceptance gates passed')
    write_json(ROOT / "APTF_TEST_014C_ACCEPTANCE_GATES_V0_1.json", gates)
    chart_dir = ROOT / "output" / "test014c_charts"
    artifacts = sorted(
        [path for path in ROOT.glob("APTF_TEST_014C_*") if path.name != "APTF_TEST_014C_ARTIFACT_HASHES_V0_1.json"]
        + list(chart_dir.glob("*.png"))
    )
    write_json(
        ROOT / "APTF_TEST_014C_ARTIFACT_HASHES_V0_1.json",
        {"files": [{"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(path), "size_bytes": path.stat().st_size} for path in artifacts]},
    )
    print(f'{gates["passed"]}/{gates["required"]} evidence-grounded acceptance gates PASS')
    print("Validation replayed: NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())