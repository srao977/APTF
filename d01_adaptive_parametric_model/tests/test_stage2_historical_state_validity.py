from __future__ import annotations

from datetime import UTC, datetime, timedelta
import math
from pathlib import Path

import pytest

from d01.v02.observations import NormalizedObservation
from d01_stage2.authority import bootstrap_seed, logical_seal, verify_authorities
from d01_stage2.evidence import build_anchor_records, write_anchor_jsonl
from d01_stage2.loader import HistoricalRow, iter_primary_csv, resolve_first_at_or_after, transition_stratum
from d01_stage2.observer import Duration, ambiguity_index, compatibility, direction_claim, observe_geometry, transition_magnitude, validity_duration
from d01_stage2.orchestration import run_evidence_tasks
from d01_stage2.replay import canonical_replay, semantic_fingerprint
from d01_stage2.scoring import censor_aware_concordance, class_contrasts, classify, moving_block_bootstrap, primary_spearman_score, score_dimension, spearman, state_c15, support_label


def rows(count: int = 8) -> list[HistoricalRow]:
    start = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    result = []
    for index in range(count):
        time = start + timedelta(minutes=index)
        price = 100.0 + index * 0.1
        observation = NormalizedObservation("SPY", time.timestamp(), time.timestamp(), index + 1, price, 1000.0, session="REGULAR", availability_mask={"price": True, "volume": True})
        result.append(HistoricalRow(index + 2, time, time, price, 1000.0, "REGULAR", observation))
    return result


def test_st2_01_frozen_direction_fallback():
    assert direction_claim(0.0, -1.0, 2.0) == -1


def test_st2_02_observer_geometry_exact():
    geometry = observe_geometry(100.0, [1, 2, 3], [101, 102, 103], 1, 3)
    assert geometry.slope > 0 and geometry.category == "CONTINUATION"


def test_st2_03_mirror_invariance():
    up = observe_geometry(100.0, [1, 2], [101, 102], 1, 2)
    down = observe_geometry(100.0, [1, 2], [10000 / 101, 10000 / 102], -1, 2)
    assert up.category == down.category and up.efficiency == pytest.approx(down.efficiency)


def test_st2_04_categories_exact_inequalities():
    assert compatibility(1, 1, -1) == "WEAKENING"
    assert compatibility(1, -1, -1) == "REVERSAL"
    assert compatibility(1, -1, 1) == "AMBIGUOUS/INCONCLUSIVE"


def test_st2_05_validity_first_prefix_reversal():
    duration = validity_duration(100, [1, 2, 3], [101, 99, 98], 1)
    assert duration.censor_type == "EXACT" and duration.lower == 2


def test_st2_06_interval_and_right_censoring():
    interval = validity_duration(100, [1, 5], [101, 99], 1, [False, True])
    right = validity_duration(100, [1, 2], [101, 102], 1)
    assert interval == Duration("INTERVAL", 1, 5) and right == Duration("RIGHT", 2, None)


def test_st2_07_elapsed_horizon_lookup():
    assert resolve_first_at_or_after([0, 60, 400], 0, 5, 1000) == (2, pytest.approx(400 / 60), "EXACT")


def test_st2_08_boundary_censors_before_lookup():
    assert resolve_first_at_or_after([0, 60], 0, 2, 100) == (None, None, "RIGHT_CENSORED")


def test_st2_09_reserve_guard_precedes_value_parse(tmp_path: Path):
    path = tmp_path / "rows.csv"
    path.write_text("event_timestamp_utc,event_timestamp_local,close,volume,session_type,data_valid\n2023-03-30T08:00:00Z,x,NOT_READ,NOT_READ,x,true\n", encoding="utf-8")
    assert list(iter_primary_csv(path)) == []


def test_st2_09b_reserve_guard_does_not_invoke_csv_parser_for_reserve(monkeypatch, tmp_path: Path):
    path = tmp_path / "rows.csv"
    path.write_text("event_timestamp_utc,event_timestamp_local,close,volume,session_type,data_valid\n2023-03-30T08:00:00Z,x,SECRET,SECRET,x,true\n", encoding="utf-8")
    import d01_stage2.loader as loader
    original = loader.csv.reader
    calls = 0
    def guarded_reader(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)
    monkeypatch.setattr(loader.csv, "reader", guarded_reader)
    assert list(iter_primary_csv(path)) == []
    assert calls == 1  # header only; reserve line is never parsed as CSV fields


def test_st2_10_input_adapter_exact_mapping(tmp_path: Path):
    path = tmp_path / "rows.csv"
    path.write_text("event_timestamp_utc,event_timestamp_local,close,volume,session_type,data_valid\n2022-09-30T08:00:00Z,x,100,20,PRE,true\n", encoding="utf-8")
    item = next(iter_primary_csv(path))
    assert item.observation.entity_id == "SPY" and item.observation.receive_time == item.observation.event_time


def test_st2_11_session_strata_priority():
    sample = rows(2)
    assert transition_stratum(None, sample[0]) == "START"
    assert transition_stratum(sample[0], sample[1]) == "INTRASESSION_CONTINUOUS"


def test_st2_12_warmup_eligibility_and_sequential_replay():
    replay, _ = canonical_replay(rows())
    assert [item["score_eligible"] for item in replay[:3]] == [False, False, True]


def test_st2_13_canonical_jsonl_logical_seal(tmp_path: Path):
    output = tmp_path / "replay.jsonl"
    replay, seal = canonical_replay(rows(), output)
    assert len(output.read_text().splitlines()) == len(replay) and len(seal) == 64


def test_st2_14_replay_determinism():
    first, _ = canonical_replay(rows())
    second, _ = canonical_replay(rows())
    assert semantic_fingerprint(first) == semantic_fingerprint(second)


def test_st2_15_ambiguity_formula_and_unavailable():
    expected = ((1 - 0.25) + 2 / 3 + 1) / 3
    assert ambiguity_index(0.25, 2, "AMBIGUOUS/INCONCLUSIVE") == pytest.approx(expected)
    assert ambiguity_index(None, 2, "REVERSAL") is None


def test_st2_16_c15_nonzero_anchors():
    result = state_c15([1, -1, 0], [2, -2, 9])
    assert result == {"concordance": 1.0, "effect": 0.5, "valid_anchors": 2}


def test_st2_17_transition_magnitude_and_spearman():
    assert transition_magnitude(3, 0.4, 10) == 5
    assert spearman([1, 2, 3], [2, 4, 8]) == pytest.approx(1)


def test_st2_18_separate_class_contrasts():
    result = class_contrasts(["REINFORCING", "CONTRADICTING", "REVERSING"], ["CONTINUATION", "WEAKENING", "REVERSAL"])
    assert result == {"delta_rc": 1.0, "delta_rv": 1.0}


def test_st2_19_exact_right_comparable_pair():
    result = censor_aware_concordance([1, 2], [Duration("EXACT", 1, 1), Duration("RIGHT", 2, None)])
    assert result["comparable_pairs"] == 1 and result["concordance"] == 1


def test_st2_20_interval_overlap_and_ties():
    overlap = censor_aware_concordance([1, 2], [Duration("INTERVAL", 1, 3), Duration("INTERVAL", 3, 5)])
    tie = censor_aware_concordance([1, 2], [Duration("EXACT", 2, 2), Duration("EXACT", 2, 2)])
    assert overlap["comparable_pairs"] == 0 and tie["concordance"] == 0.5


def test_st2_21_reversal_orientation_negative():
    durations = [Duration("EXACT", 1, 1), Duration("EXACT", 3, 3)]
    assert censor_aware_concordance([2, 1], durations, reverse_orientation=True)["concordance"] == 1


def test_st2_22_support_and_four_level_classification():
    assert [support_label(value) for value in (9, 10, 30)] == ["INSUFFICIENT", "LIMITED", "ADEQUATE"]
    assert classify(0.2, (0.1, 0.3), "ADEQUATE") == "EMPIRICALLY_SUPPORTED"
    assert classify(-0.2, (-0.3, -0.1), "ADEQUATE") == "UNSUPPORTED"


def test_st2_23_deterministic_moving_block_bootstrap():
    records = [{"block_id": index, "value": float(index)} for index in range(12)]
    statistic = lambda sample: sum(float(row["value"]) for row in sample) / len(sample)
    first = moving_block_bootstrap(records, statistic, replicates=50)
    second = moving_block_bootstrap(records, statistic, replicates=50)
    assert first == second and bootstrap_seed() == bootstrap_seed()


def test_st2_24_process_smoke_real_multiple_pids():
    evidence = run_evidence_tasks(4, max_workers=3, smoke_delay=0.05)
    assert evidence["unique_worker_count"] >= 2
    assert all(item["pid"] != item["parent_pid"] for item in evidence["tasks"])


def v022_records() -> list[dict[str, object]]:
    return [
        {"anchor_id": 1, "score_eligible": True, "block_id": 0, "strength": 1.0, "coherence": 1.0, "uncertainty": 1.0, "strength_expression": 2.0, "efficiency": 0.2, "ambiguity_index": 0.1, "fixed": {"5m": {"efficiency": 0.9}}},
        {"anchor_id": 2, "score_eligible": True, "block_id": 1, "strength": 2.0, "coherence": 2.0, "uncertainty": 2.0, "strength_expression": 4.0, "efficiency": 0.4, "ambiguity_index": 0.2, "fixed": {"5m": {"efficiency": 0.1}}},
        {"anchor_id": 3, "score_eligible": True, "block_id": 2, "strength": 3.0, "coherence": 3.0, "uncertainty": 3.0, "strength_expression": 6.0, "efficiency": 0.6, "ambiguity_index": 0.3, "fixed": {"5m": {"efficiency": 0.8}}},
        {"anchor_id": 4, "score_eligible": False, "block_id": 3, "strength": 99.0, "coherence": 99.0, "uncertainty": 99.0, "strength_expression": -99.0, "efficiency": -99.0, "ambiguity_index": -99.0},
    ]


def test_st2_25_v022_authority_guard_passes_without_value_read():
    workspace = Path(__file__).resolve().parents[2]
    result = verify_authorities(workspace, include_dataset=False)
    assert result["scoring_v022_freeze_id"] == "D01_STAGE2_SCORING_V0_2_2_FROZEN_20260815T185154Z"
    assert result["reserve_accessed"] is False


def test_st2_26_v022_primary_15m_strength_coherence_uncertainty():
    results = {dimension: primary_spearman_score(dimension, v022_records()) for dimension in ("strength", "coherence", "uncertainty")}
    assert all(result["primary_coordinate"] == "fixed_15m" and result["effect"] == pytest.approx(1.0) for result in results.values())


def test_st2_27_v022_no_pooling_or_best_horizon_selection():
    result = primary_spearman_score("coherence", v022_records())
    assert result["pooled_horizons"] is False and result["best_horizon_selection"] is False


def test_st2_28_v022_missing_excludes_relevant_statistic_only():
    records = v022_records()
    records[1]["ambiguity_index"] = None
    records[1]["uncertainty_exclusion_reason"] = "AMBIGUITY_COMPONENT_UNAVAILABLE"
    uncertainty = primary_spearman_score("uncertainty", records)
    coherence = primary_spearman_score("coherence", records)
    assert uncertainty["available_records"] == 2 and uncertainty["exclusion_counts"] == {"AMBIGUITY_COMPONENT_UNAVAILABLE": 1}
    assert coherence["available_records"] == 3


def test_st2_29_v022_existing_anchor_population_retained():
    records = v022_records()
    records[0]["strength_expression"] = None
    result = primary_spearman_score("strength", records)
    assert result["eligible_anchors"] == 3 and result["available_records"] == 2 and result["excluded_records"] == 1


def test_st2_30_v022_one_anchor_one_record_weighting_guard():
    records = v022_records()
    records.insert(1, dict(records[0]))
    with pytest.raises(ValueError, match="DUPLICATE_ANCHOR_RECORD"):
        primary_spearman_score("strength", records)


def test_st2_31_v022_secondary_does_not_change_primary():
    records = v022_records()
    before = primary_spearman_score("coherence", records)
    for record in records[:3]:
        record["fixed"]["5m"]["efficiency"] *= -100
    after = primary_spearman_score("coherence", records)
    assert before == after


def test_st2_32_all_dimensions_have_scientific_scorers():
    replay, _ = canonical_replay(rows(30))
    anchors = build_anchor_records(replay)
    from d01_stage2.constants import DIMENSIONS
    results = [score_dimension(dimension, anchors, replicates=4) for dimension in DIMENSIONS]
    assert len(results) == 11 and all("classification" in result for result in results)


def test_st2_33_process_workers_score_read_only_dimensions(tmp_path: Path):
    replay, _ = canonical_replay(rows(45))
    anchors = build_anchor_records(replay)
    path = tmp_path / "anchors.jsonl"
    write_anchor_jsonl(path, anchors, {"kind": "test"})
    evidence = run_evidence_tasks(len(anchors), max_workers=3, evidence_path=str(path), replicates=4)
    assert evidence["mode"] == "dimension_scoring" and evidence["unique_worker_count"] >= 2 and evidence["peak_concurrency"] >= 2
    assert all(task["result"] is not None for task in evidence["tasks"])