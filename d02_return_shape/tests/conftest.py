import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
for path in (ROOT / "src", WORKSPACE / "d01_adaptive_parametric_model" / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))