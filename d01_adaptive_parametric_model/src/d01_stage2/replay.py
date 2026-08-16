from __future__ import annotations

import json
import hashlib
import math
from pathlib import Path
from typing import Iterable

from d01.v02.model import D01V02Model

from .authority import canonical_json, logical_seal
from .loader import HistoricalRow, transition_stratum


CORE_DMO_FIELDS = ("state_level", "state_velocity", "state_acceleration", "state_curvature", "strength", "coherence", "persistence", "uncertainty", "reversal_propensity", "observation_half_life", "forward_half_life")


def _compact_record(record: dict[str, object]) -> dict[str, object]:
    dmo = record["dmo"]
    return {
        **{key: record[key] for key in ("source_row_id", "accepted_index", "event_time", "close", "session", "transition_stratum", "adaptive_reference", "adaptive_scale", "score_eligible")},
        "dmo": {key: dmo[key] for key in CORE_DMO_FIELDS + ("perturbation_magnitude", "perturbation_class", "model_health", "config_hash", "state_hash", "trace_id")},
        "fmo": {"interval_length": record["fmo"]["interval_length"]},
    }


def canonical_replay(rows: Iterable[HistoricalRow], output_path: Path | None = None, checkpoint_path: Path | None = None, checkpoint_every: int = 10000, compact: bool = False, metadata: dict[str, object] | None = None, progress: callable | None = None) -> tuple[list[dict[str, object]], str]:
    model = D01V02Model(entity_id="SPY")
    records: list[dict[str, object]] = []
    previous: HistoricalRow | None = None
    output = output_path.open("w", encoding="utf-8", newline="\n") if output_path else None
    logical_digest = hashlib.sha256()
    semantic_digest = hashlib.sha256()
    try:
        for accepted_index, row in enumerate(rows, start=1):
            dmo, fmo = model.step(row.observation)
            dmo_payload, fmo_payload = dmo.to_dict(), fmo.to_dict()
            if dmo.model_health == "INVALID" or any(not math.isfinite(float(dmo_payload[field])) for field in CORE_DMO_FIELDS):
                raise RuntimeError("REPLAY_INTEGRITY_FAILURE")
            adaptive_reference = float(model.state.adaptive_reference)
            adaptive_scale = float(model.state.adaptive_scale)
            readiness_finite = math.isfinite(adaptive_reference) and math.isfinite(adaptive_scale)
            record = {
                "source_row_id": row.source_row_id, "accepted_index": accepted_index,
                "event_time": row.event_time.isoformat(), "close": row.close, "session": row.session,
                "transition_stratum": transition_stratum(previous, row),
                "adaptive_reference": adaptive_reference, "adaptive_scale": adaptive_scale,
                "score_eligible": accepted_index >= 3 and readiness_finite and adaptive_scale >= model.config.reference.min_scale and dmo.model_health != "INVALID",
                "dmo": dmo_payload, "fmo": fmo_payload,
            }
            records.append(_compact_record(record) if compact else record)
            encoded = canonical_json(record).encode("utf-8")
            logical_digest.update(encoded)
            logical_digest.update(b"\n")
            reduced = {
                "source_row_id": record["source_row_id"], "state_hash": dmo_payload["state_hash"],
                "trace_id": dmo_payload["trace_id"], "config_hash": dmo_payload["config_hash"],
                "state": [dmo_payload[key] for key in CORE_DMO_FIELDS], "fmo": fmo_payload,
            }
            semantic_digest.update(canonical_json(reduced).encode("utf-8"))
            semantic_digest.update(b"\n")
            if output:
                output.write(encoded.decode("utf-8") + "\n")
            if checkpoint_path and accepted_index % checkpoint_every == 0:
                checkpoint_path.write_text(json.dumps({"accepted_index": accepted_index, "prefix_sha256": logical_digest.hexdigest().upper(), "recovery_policy": "RESTART_PHASE_B_FROM_INITIAL_STATE", "partial_artifact_accepted": False}, sort_keys=True), encoding="utf-8")
            if progress and accepted_index % checkpoint_every == 0:
                progress(accepted_index)
            previous = row
    finally:
        if output:
            output.close()
    authority = {"model": "D01 v0.2", "record_count": len(records), "config_hash": records[-1]["dmo"]["config_hash"] if records else None}
    logical_digest.update(canonical_json(authority).encode("utf-8"))
    semantic_digest.update(canonical_json({"kind": "semantic_fingerprint"}).encode("utf-8"))
    if metadata is not None:
        metadata.update({"record_count": len(records), "semantic_fingerprint": semantic_digest.hexdigest().upper(), "recovery_policy": "RESTART_PHASE_B_FROM_INITIAL_STATE"})
    if checkpoint_path and checkpoint_path.exists():
        checkpoint_path.write_text(json.dumps({"accepted_index": len(records), "logical_seal": logical_digest.hexdigest().upper(), "semantic_fingerprint": semantic_digest.hexdigest().upper(), "phase_complete": True}, sort_keys=True), encoding="utf-8")
    return records, logical_digest.hexdigest().upper()


def semantic_fingerprint(records: list[dict[str, object]]) -> str:
    reduced = [{
        "source_row_id": row["source_row_id"], "state_hash": row["dmo"]["state_hash"],
        "trace_id": row["dmo"]["trace_id"], "config_hash": row["dmo"]["config_hash"],
        "state": [row["dmo"][key] for key in CORE_DMO_FIELDS], "fmo": row["fmo"],
    } for row in records]
    return logical_seal(reduced, {"kind": "semantic_fingerprint"})