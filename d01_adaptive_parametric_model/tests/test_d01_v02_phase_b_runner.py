from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


def test_phase_b_preflight_executes(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    script = repo / "scripts" / "run_d01_v02_phase_b.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--workers", "2"],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode in (0, 1)
    assert "decision" in proc.stdout

    manifest = repo / "output" / "d01_v02_phase_b" / "manifests" / "v02_phase_b_preflight_manifest.json"
    assert manifest.exists()
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["mode"] == "PREFLIGHT_ONLY"
    assert payload["full_run_launched_by_chat"] is False
