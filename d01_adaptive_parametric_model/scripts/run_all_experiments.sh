#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m aptf_d01.cli.main run-matrix
python -m aptf_d01.cli.main summarize
