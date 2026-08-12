from __future__ import annotations

from pathlib import Path

import yaml


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_scenario(path: Path) -> dict:
    data = load_yaml(path)
    if "name" not in data:
        raise ValueError(f"Scenario missing name: {path}")
    if "steps" not in data or not isinstance(data["steps"], list):
        raise ValueError(f"Scenario missing steps list: {path}")
    return data
