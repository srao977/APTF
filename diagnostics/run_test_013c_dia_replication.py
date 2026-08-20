from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

import run_test_013b_qqq_validation as frozen


ROOT = Path(__file__).resolve().parents[1]
DIA_SOURCE = ROOT / "DIA_1min_firstratedata.csv"
QQQ_SOURCE = ROOT / "QQQ_1min_firstratedata.csv"
SPY_SOURCE = ROOT / "data" / "market" / "normalized" / "SPY_1min_normalized_v0_1.csv"
SPY_SCORE = ROOT / "APTF_TEST_012_FP_VECTOR_FIELD_SCORECARD_V0_1.csv"
QQQ_SCORE = ROOT / "APTF_TEST_013B_QQQ_PRIMARY_SCORECARD_V0_1.csv"
QQQ_CROSS = ROOT / "APTF_TEST_013B_SPY_VS_QQQ_GENERALIZATION_V0_1.csv"
LOCAL_ZONE = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


def read_raw(path: Path):
    return list(csv.DictReader(path.open(newline="", encoding="utf-8-sig")))


def source_characteristics(instrument: str, rows: list[dict[str, str]], timestamp_field: str, price_field: str, normalized: bool = False):
    if normalized:
        timestamps = [datetime.fromisoformat(row[timestamp_field]) for row in rows]
    else:
        timestamps = [datetime.fromisoformat(row[timestamp_field]).replace(tzinfo=LOCAL_ZONE) for row in rows]
    prices = np.asarray([float(row[price_field]) for row in rows])
    contiguous_indices = []
    for index in range(1, len(rows)):
        if normalized:
            same_session = rows[index - 1]["session_type"] == rows[index]["session_type"]
            same_date = rows[index - 1]["event_timestamp_local"][:10] == rows[index]["event_timestamp_local"][:10]
            elapsed = (timestamps[index] - timestamps[index - 1]).total_seconds()
            eligible = same_session and same_date and elapsed == 60.0
        else:
            sessions = (frozen.session_type(timestamps[index - 1]), frozen.session_type(timestamps[index]))
            eligible = timestamps[index - 1].date() == timestamps[index].date() and sessions[0] == sessions[1] and sessions[0] != "OUTSIDE" and (timestamps[index] - timestamps[index - 1]).total_seconds() == 60.0
        if eligible:
            contiguous_indices.append(index)
    changes = np.asarray([prices[index] - prices[index - 1] for index in contiguous_indices])
    absolute = np.abs(changes)
    relative = np.asarray([abs(prices[index] - prices[index - 1]) / abs(prices[index - 1]) for index in contiguous_indices])
    nonzero = absolute[absolute > 0]
    decimal_places = max(max(0, -Decimal(rows[index][price_field]).as_tuple().exponent) for index in range(len(rows)))
    increments = Counter(str(Decimal(rows[index][price_field]) - Decimal(rows[index - 1][price_field])) for index in contiguous_indices if Decimal(rows[index][price_field]) != Decimal(rows[index - 1][price_field]))
    common = [{"increment": increment, "count": count} for increment, count in increments.most_common(10)]
    return {
        "instrument": instrument, "source_rows": len(rows), "eligible_price_pairs": len(contiguous_indices),
        "unchanged_count": int(np.sum(absolute == 0)), "unchanged_percentage": float(np.mean(absolute == 0)),
        "nonzero_count": int(np.sum(absolute > 0)), "nonzero_percentage": float(np.mean(absolute > 0)),
        "abs_movement_Q25": float(np.quantile(absolute, .25)), "abs_movement_median": float(np.median(absolute)),
        "abs_movement_Q75": float(np.quantile(absolute, .75)), "abs_movement_Q90": float(np.quantile(absolute, .90)),
        "abs_movement_Q95": float(np.quantile(absolute, .95)), "abs_movement_Q99": float(np.quantile(absolute, .99)),
        "abs_movement_maximum": float(absolute.max()), "relative_movement_median": float(np.median(relative)),
        "relative_movement_Q90": float(np.quantile(relative, .90)), "relative_movement_Q95": float(np.quantile(relative, .95)),
        "relative_movement_Q99": float(np.quantile(relative, .99)), "source_decimal_places_max": decimal_places,
        "smallest_nonzero_increment": float(nonzero.min()), "most_common_signed_nonzero_increments_json": json.dumps(common, separators=(",", ":")),
    }, contiguous_indices, changes


def score_stratum(label: str, model: str, rows: list[dict[str, object]]):
    successful = [row for row in rows if row["RK_success"] == "true"]
    errors = np.asarray([float(row["error_P2"]) for row in successful])
    return {
        "stratum": label, "model": model, "count": len(successful),
        "P2_MAE": float(np.mean(np.abs(errors))), "P2_RMSE": float(np.sqrt(np.mean(errors ** 2))),
        "P2_sign_accuracy": float(np.mean([row["projected_P2_sign"] == row["actual_P2_sign"] for row in successful])),
        "derivative_state_accuracy": float(np.mean([row["predicted_derivative_state"] == row["actual_derivative_state"] for row in successful])),
        "domain_exit_rate": float(np.mean([row["envelope_exit"] == "true" for row in successful])),
    }


def main() -> int:
    raw = read_raw(DIA_SOURCE)
    timestamps = [row["timestamp"] for row in raw]
    local_times = [datetime.fromisoformat(value).replace(tzinfo=LOCAL_ZONE) for value in timestamps]
    utc_times = [value.astimezone(UTC) for value in local_times]
    times_minutes = np.asarray([value.timestamp() / 60.0 for value in utc_times])
    sessions = [frozen.session_type(value) for value in local_times]
    p = np.asarray([float(row["close"]) for row in raw])
    p1, p2, derivative_failures = frozen.causal_quadratic(times_minutes, p)
    jp = np.full(len(p), np.nan)
    projection_eligible = []
    for index in range(1, len(p)):
        if frozen.contiguous(index - 1, index, local_times, sessions) and np.isfinite(p2[index - 1]) and np.isfinite(p2[index]):
            jp[index] = p2[index] - p2[index - 1]
    for index in range(14, len(p) - 1):
        if frozen.contiguous(index, index + 1, local_times, sessions) and np.all(np.isfinite([p1[index], p2[index], p1[index + 1], p2[index + 1]])):
            projection_eligible.append(index)

    dia_characteristics, dia_pairs, _ = source_characteristics("DIA", raw, "timestamp", "close")
    qqq_characteristics, _, _ = source_characteristics("QQQ", read_raw(QQQ_SOURCE), "timestamp", "close")
    spy_characteristics, _, _ = source_characteristics("SPY", read_raw(SPY_SOURCE), "event_timestamp_utc", "close", normalized=True)
    characteristics = [spy_characteristics, qqq_characteristics, dia_characteristics]

    absolute_p1 = np.abs(p1[np.isfinite(p1)])
    absolute_p2 = np.abs(p2[np.isfinite(p2)])
    for name, values in (("P1", absolute_p1), ("P2", absolute_p2)):
        dia_characteristics[f"abs_{name}_median"] = float(np.median(values))
        for probability, suffix in ((.90, "Q90"), (.95, "Q95"), (.99, "Q99")):
            dia_characteristics[f"abs_{name}_{suffix}"] = float(np.quantile(values, probability))
        dia_characteristics[f"abs_{name}_maximum"] = float(values.max())

    f0 = frozen.fit_f0(p, p1, p2, jp, times_minutes)
    f4 = {window: frozen.fit_f4(p, p1, p2, jp, window) for window in frozen.WINDOWS}
    f0_cover = {index for index in projection_eligible if frozen.valid_fit(f0, index)}
    f4_cover = {window: {index for index in projection_eligible if frozen.valid_fit(f4[window], index)} for window in frozen.WINDOWS}
    primary_cover = sorted(f0_cover & f4_cover[30])
    sensitivity_cover = sorted(f4_cover[15] & f4_cover[30] & f4_cover[60])
    if not primary_cover:
        raise RuntimeError("SECOND_EXTERNAL_REPLICATION_BLOCKED_EMPTY_PRIMARY_COVER")

    solved_f0, failed_f0 = frozen.solve_cover(primary_cover, f0, p, p1, p2, True)
    solved_w30, failed_w30 = frozen.solve_cover(primary_cover, f4[30], p, p1, p2, False)
    primary_f0, jac_f0, domain_f0, causal_f0 = frozen.projection_rows("F0_W15", primary_cover, f0, solved_f0, failed_f0, timestamps, sessions, p, p1, p2)
    primary_w30, jac_w30, domain_w30, causal_w30 = frozen.projection_rows("F4_L1_W30", primary_cover, f4[30], solved_w30, failed_w30, timestamps, sessions, p, p1, p2)
    for row in primary_f0 + primary_w30:
        row["instrument"] = "DIA"
    pert_f0 = frozen.perturbation_rows("F0_W15", "PRIMARY", primary_cover, f0)
    pert_w30 = frozen.perturbation_rows("F4_L1_W30", "PRIMARY", primary_cover, f4[30])
    for row in pert_f0 + pert_w30:
        row["instrument"] = "DIA"
    score_f0, upper_f0, lower_f0 = frozen.score("F0_W15", primary_f0, len(failed_f0), pert_f0)
    score_w30, upper_w30, lower_w30 = frozen.score("F4_L1_W30", primary_w30, len(failed_w30), pert_w30)
    for row in (score_f0, score_w30):
        row["instrument"] = "DIA"

    sensitivity_scores = []
    sensitivity_perturbations = []
    if sensitivity_cover:
        for window in frozen.WINDOWS:
            model = f"F4_L1_W{window}"
            solved, failed = frozen.solve_cover(sensitivity_cover, f4[window], p, p1, p2, False)
            rows, _, _, _ = frozen.projection_rows(model, sensitivity_cover, f4[window], solved, failed, timestamps, sessions, p, p1, p2)
            perturbations = frozen.perturbation_rows(model, "SENSITIVITY", sensitivity_cover, f4[window])
            for row in rows + perturbations:
                row["instrument"] = "DIA"
            scored, _, _ = frozen.score(model, rows, len(failed), perturbations)
            scored["instrument"] = "DIA"
            sensitivity_scores.append(scored)
            sensitivity_perturbations.extend(perturbations)

    coefficient_rows = []
    for index in primary_cover:
        beta = f4[30]["standardized"][index]
        physical = f4[30]["physical"][index]
        coefficient_rows.append({
            "instrument":"DIA","model":"F4_L1_W30","observation_index":index+1,"timestamp":timestamps[index],
            "b0":beta[0],"b1":beta[1],"b2":beta[2],"b3":beta[3],"physical_intercept":physical[0],
            "physical_a1":physical[1],"physical_a2":physical[2],"physical_a3":physical[3],
            "coefficient_norm":float(np.linalg.norm(beta)),
            "state_center_json":json.dumps(f4[30]["means"][index].tolist(),separators=(",",":")),
            "state_scale_json":json.dumps(f4[30]["scales"][index].tolist(),separators=(",",":")),
            "condition_number":f4[30]["condition"][index],
        })

    by_model = {"F0_W15": primary_f0, "F4_L1_W30": primary_w30}
    movements = np.asarray([abs(p[index + 1] - p[index]) for index in primary_cover])
    boundaries = np.quantile(movements, [.25, .50, .75, .90, .99])
    labels = ["Q0-Q25", "Q25-Q50", "Q50-Q75", "Q75-Q90", "Q90-Q99", "Q99-Q100"]
    movement_rows = []
    for model, rows in by_model.items():
        row_by_observation = {int(row["observation_index"]) - 1: row for row in rows}
        band_indices = [[] for _ in labels]
        for index, movement in zip(primary_cover, movements):
            band = int(np.searchsorted(boundaries, movement, side="right"))
            band_indices[band].append(index)
        for label, indices in zip(labels, band_indices):
            if indices:
                movement_rows.append(score_stratum(label, model, [row_by_observation[index] for index in indices]))

    zero_rows = []
    for model, rows in by_model.items():
        groups = {
            "EXACT_ZERO_MOVEMENT": [row for row in rows if float(row["actual_P"]) == float(row["P"])],
            "NONZERO_MOVEMENT": [row for row in rows if float(row["actual_P"]) != float(row["P"])],
            "NEAR_ZERO_DERIVATIVE_STATE": [row for row in rows if abs(float(row["P1"])) <= frozen.EPSILON],
            "NON_NEAR_ZERO_DERIVATIVE_STATE": [row for row in rows if abs(float(row["P1"])) > frozen.EPSILON],
        }
        for label, rows_in_group in groups.items():
            if rows_in_group:
                zero_rows.append(score_stratum(label, model, rows_in_group))

    spy_score = {row["candidate_id"]: row for row in csv.DictReader(SPY_SCORE.open(newline="",encoding="utf-8"))}
    qqq_score = {row["model"]: row for row in csv.DictReader(QQQ_SCORE.open(newline="",encoding="utf-8"))}
    dia_score = {row["model"]: row for row in (score_f0, score_w30)}
    metrics = {
        "P2_MAE":("P2_MAE","P2_MAE"),"P2_RMSE":("P2_RMSE","P2_RMSE"),"P2_Q99":("P2_Q99","P2_Q99"),
        "P2_Q99_9":("P2_Q99_9","P2_Q99_9"),"P2_max_abs_error":("P2_max_abs_error","P2_max_abs_error"),
        "P2_sign_accuracy":("P2_sign_accuracy","P2_sign_accuracy"),
        "derivative_state_accuracy":("derivative_state_accuracy","derivative_state_accuracy"),
        "perturbation_Q99":("perturbation_Q99","perturbation_Q99"),
        "domain_exit_rate":("local_envelope_exit_rate","domain_exit_rate"),
        "max_real_eigenvalue_Q99":("Q99_max_real_eigenvalue","max_real_eigenvalue_Q99"),
    }
    generalization = []
    for metric,(spy_key,other_key) in metrics.items():
        output={"metric":metric}
        for instrument,table in (("SPY",spy_score),("QQQ",qqq_score),("DIA",dia_score)):
            key=spy_key if instrument=="SPY" else other_key
            f0=float(table["F0_W15"][key]);f4=float(table["F4_L1_W30"][key])
            output[f"{instrument}_F0"]=f0;output[f"{instrument}_F4"]=f4
            output[f"{instrument}_absolute_change"]=f4-f0
            output[f"{instrument}_relative_change"]=None if f0==0 else (f4-f0)/abs(f0)
        generalization.append(output)

    transitions={"test_id":"APTF_TEST_013C_DIA_TRANSITION_VALIDATION_V0_1","F0_W15":{"upper":upper_f0,"lower":lower_f0},"F4_L1_W30":{"upper":upper_w30,"lower":lower_w30},"definitions":"endpoint P1 sign crossing under frozen authority"}
    state_summary={
        "test_id":"APTF_TEST_013C_DIA_STATE_CONSTRUCTION_SUMMARY_V0_1","total_rows":len(raw),"initialization_rows":14,
        "derivative_fit_failures":derivative_failures,"complete_state_rows":int(np.sum(np.isfinite(p1)&np.isfinite(p2))),
        "contiguous_jp_targets":int(np.sum(np.isfinite(jp))),"eligible_contiguous_projection_origins":len(projection_eligible),
        "F0_eligible_rows":len(f0_cover),"F4_W15_eligible_rows":len(f4_cover[15]),"F4_W30_eligible_rows":len(f4_cover[30]),
        "F4_W60_eligible_rows":len(f4_cover[60]),"primary_common_cover":len(primary_cover),
        "primary_sessions_represented":len({local_times[index].date() for index in primary_cover}),
        "sensitivity_common_cover":len(sensitivity_cover),"sensitivity_sessions_represented":len({local_times[index].date() for index in sensitivity_cover}),
    }

    characteristic_fields = list(dict.fromkeys(key for row in characteristics for key in row))
    frozen.write_csv(ROOT/"APTF_TEST_013C_DIA_TRAJECTORY_CHARACTERISTICS_V0_1.csv",characteristics,characteristic_fields)
    frozen.write_csv(ROOT/"APTF_TEST_013C_PRICE_PRECISION_AUDIT_V0_1.csv",characteristics,characteristic_fields)
    frozen.write_csv(ROOT/"APTF_TEST_013C_DIA_PRIMARY_PROJECTIONS_V0_1.csv",primary_f0+primary_w30,frozen.PRIMARY_COLUMNS)
    frozen.write_csv(ROOT/"APTF_TEST_013C_DIA_PRIMARY_SCORECARD_V0_1.csv",[score_f0,score_w30])
    frozen.write_csv(ROOT/"APTF_TEST_013C_DIA_MOVEMENT_BAND_SCORECARD_V0_1.csv",movement_rows)
    frozen.write_csv(ROOT/"APTF_TEST_013C_DIA_ZERO_MOVEMENT_DIAGNOSTIC_V0_1.csv",zero_rows)
    if sensitivity_scores:frozen.write_csv(ROOT/"APTF_TEST_013C_DIA_WINDOW_SENSITIVITY_SCORECARD_V0_1.csv",sensitivity_scores)
    else:(ROOT/"APTF_TEST_013C_DIA_WINDOW_SENSITIVITY_SCORECARD_V0_1.csv").write_text("status,reason\nBLOCKED,EMPTY_COMMON_COVER\n",encoding="utf-8")
    frozen.write_csv(ROOT/"APTF_TEST_013C_SPY_QQQ_DIA_GENERALIZATION_V0_1.csv",generalization)
    frozen.write_csv(ROOT/"APTF_TEST_013C_DIA_PERTURBATION_STABILITY_V0_1.csv",pert_f0+pert_w30+sensitivity_perturbations)
    frozen.write_csv(ROOT/"APTF_TEST_013C_DIA_JACOBIAN_STABILITY_V0_1.csv",jac_f0+jac_w30)
    frozen.write_csv(ROOT/"APTF_TEST_013C_DIA_LOCAL_DOMAIN_VALIDATION_V0_1.csv",domain_f0+domain_w30)
    frozen.write_csv(ROOT/"APTF_TEST_013C_DIA_F4_COEFFICIENT_STABILITY_V0_1.csv",coefficient_rows)
    frozen.write_csv(ROOT/"APTF_TEST_013C_DIA_CAUSALITY_AUDIT_V0_1.csv",causal_f0+causal_w30)
    (ROOT/"APTF_TEST_013C_DIA_TRANSITION_VALIDATION_V0_1.json").write_text(json.dumps(transitions,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (ROOT/"APTF_TEST_013C_DIA_STATE_CONSTRUCTION_SUMMARY_V0_1.json").write_text(json.dumps(state_summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"characteristics":dia_characteristics,"state":state_summary},indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())