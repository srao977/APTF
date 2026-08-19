from __future__ import annotations

import hashlib
import json
import math
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, Mapping

try:
    from pydantic import BaseModel
except ImportError:  # pragma: no cover - pydantic is a declared dependency
    BaseModel = ()  # type: ignore[assignment,misc]


CANONICAL_PROFILE = "APTF-CJSON-V1"


def normalize_semantic(value: Any) -> Any:
    """Convert a frozen semantic payload into APTF-CJSON-V1 JSON values."""
    if isinstance(value, BaseModel):
        return normalize_semantic(value.model_dump(mode="python"))
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: normalize_semantic(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Enum):
        return normalize_semantic(value.value)
    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("APTF-CJSON-V1 requires string mapping keys")
            if key in normalized:
                raise ValueError(f"duplicate mapping key: {key}")
            normalized[key] = normalize_semantic(item)
        return normalized
    if isinstance(value, (list, tuple)):
        return [normalize_semantic(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("APTF-CJSON-V1 rejects non-finite floats")
        return 0.0 if value == 0.0 else value
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise TypeError(f"unsupported semantic payload type: {type(value).__name__}")


def canonical_json_text(value: Any) -> str:
    normalized = normalize_semantic(value)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def canonical_json_bytes(value: Any) -> bytes:
    return canonical_json_text(value).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()
