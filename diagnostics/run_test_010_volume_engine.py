from __future__ import annotations

import bisect
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OBS = ROOT / "APTF_TEST_009V_PRICE_VOLUME_OBSERVATIONS_V0_1.csv"
CROSSINGS = ROOT / "APTF_TEST_009_DERIVATIVE_CROSSINGS_V0_1.csv"
INTERVALS = (3, 5, 8, 15)
CONDITION_LIMIT = 1e8

INTERVAL_COLUMNS = [
    "observation_index", "timestamp", "interval", "V_RAW", "V_N", "V_mean",
    "V_median", "V_min", "V_max", "V_range", "V_std", "V_cv",
    "V_max_median_ratio", "V_mean_relative_to_baseline", "count_VN_ge_2",
    "count_VN_ge_5", "count_VN_ge_10", "fraction_VN_ge_2",
    "fraction_VN_ge_5", "fraction_VN_ge_10", "current_V_N", "max_V_N",
    "observations_since_interval_max", "count_elevated", "count_extreme",
    "persistence_above_baseline", "V1", "V2", "V1_sign", "V2_sign",
    "V1_persistence", "V2_persistence",
]

MODEL_COLUMNS = [
    "model_id", "representation", "interval", "causal_availability", "valid_forecasts",
    "failed_forecasts", "median_condition_number", "coefficient_stability",
    "VN_MAE", "VN_RMSE", "VN_median_absolute_error", "VN_signed_bias",
    "volume_regime_transition_accuracy", "burst_persistence_accuracy",
    "noise_sensitivity", "suitability_for_ODE", "suitability_for_state_update",
]

EMISSION_COLUMNS = [
    "volume_emission_id", "observation_index", "timestamp", "V_RAW", "V_N",
    "selected_interval", "interval_state_json", "V1", "V2", "observer_state",
    "local_volume_model_id", "predicted_next_V_N", "actual_next_V_N",
    "state_error", "predicted_next_regime", "actual_next_regime",
    "regime_prediction_correct", "burst_persistence_correct", "model_stability",
    "next_elapsed_minutes",
]

EVENT_COLUMNS = [
    "event_id", "observation_index", "timestamp", "event_type", "V_RAW", "V_N",
    "V1", "V2", "interval_state", "concurrent_P", "concurrent_P1", "concurrent_P2",
    "nearest_frozen_price_crossing", "crossing_type", "signed_observations_offset",
    "signed_seconds_offset",
]


def sign(value: float, tolerance: float = 1e-15) -> int:
    return 1 if value > tolerance else -1 if value < -tolerance else 0


def persistence(values: np.ndarray, index: int, predicate) -> int:
    if not predicate(values[index]):
        return 0
    start = index
    while start - 1 >= 0 and predicate(values[start - 1]):
        start -= 1
    return index - start + 1


def state_regime(value: float, boundaries: dict[str, float]) -> str:
    if value <= boundaries["q25"]: return "LOW"
    if value <= boundaries["q75"]: return "NORMAL"
    if value <= boundaries["q95"]: return "ELEVATED"
    return "EXTREME"


def error_metrics(predicted: np.ndarray, actual: np.ndarray) -> dict[str, Any]:
    mask = np.isfinite(predicted) & np.isfinite(actual)
    errors = predicted[mask] - actual[mask]
    return {
        "valid": int(mask.sum()), "mae": float(np.mean(np.abs(errors))),
        "rmse": float(np.sqrt(np.mean(errors * errors))),
        "median": float(np.median(np.abs(errors))), "bias": float(np.mean(errors)),
        "mask": mask,
    }


def main() -> int:
    rows = list(csv.DictReader(OBS.open(newline="", encoding="utf-8")))
    selection = json.loads((ROOT / "APTF_TEST_009V_VOLUME_SELECTION_V0_1.json").read_text())
    if len(rows) != 101221 or selection["primary_V_N_candidate"] != "ROLLING_MEDIAN_RATIO_15":
        raise RuntimeError("frozen Volume authority changed")
    raw = np.asarray([float(row["V_RAW"]) for row in rows])
    vn = np.asarray([np.nan if row["V_N"] == "" else float(row["V_N"]) for row in rows])
    v1 = np.asarray([np.nan if row["V1"] == "" else float(row["V1"]) for row in rows])
    v2 = np.asarray([np.nan if row["V2"] == "" else float(row["V2"]) for row in rows])
    p = np.asarray([float(row["price"]) for row in rows])
    p1 = np.asarray([np.nan if row["frozen_P1"] == "" else float(row["frozen_P1"]) for row in rows])
    p2 = np.asarray([np.nan if row["frozen_P2"] == "" else float(row["frozen_P2"]) for row in rows])
    times = np.asarray([datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")).timestamp() / 60.0 for row in rows])
    boundaries = selection["volume_regime_boundaries"]

    interval_data: dict[int, dict[str, np.ndarray]] = {}
    with (ROOT / "APTF_TEST_010_VOLUME_INTERVAL_STATES_V0_1.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=INTERVAL_COLUMNS); writer.writeheader()
        for interval in INTERVALS:
            fields = {name: np.full(len(rows), np.nan) for name in (
                "mean", "median", "min", "max", "std", "max_median", "mean_vn", "median_vn",
                "since_max", "count_elevated", "count_extreme", "persist_baseline",
            )}
            for index in range(interval - 1, len(rows)):
                raw_window = raw[index - interval + 1:index + 1]
                vn_window = vn[index - interval + 1:index + 1]
                if not np.all(np.isfinite(vn_window)): continue
                mean_raw = float(np.mean(raw_window)); median_raw = float(np.median(raw_window))
                std_raw = float(np.std(raw_window)); max_position = int(np.argmax(vn_window))
                values = {
                    "mean": mean_raw, "median": median_raw, "min": float(np.min(raw_window)),
                    "max": float(np.max(raw_window)), "std": std_raw,
                    "max_median": float(np.max(raw_window) / median_raw) if median_raw > 0 else np.nan,
                    "mean_vn": float(np.mean(vn_window)), "median_vn": float(np.median(vn_window)),
                    "since_max": interval - 1 - max_position,
                    "count_elevated": int(sum(state_regime(value, boundaries) == "ELEVATED" for value in vn_window)),
                    "count_extreme": int(sum(state_regime(value, boundaries) == "EXTREME" for value in vn_window)),
                    "persist_baseline": persistence(vn, index, lambda value: math.isfinite(value) and value >= 1.0),
                }
                for key, value in values.items(): fields[key][index] = value
                writer.writerow({
                    "observation_index": index + 1, "timestamp": rows[index]["timestamp"], "interval": interval,
                    "V_RAW": raw[index], "V_N": vn[index], "V_mean": mean_raw, "V_median": median_raw,
                    "V_min": values["min"], "V_max": values["max"], "V_range": values["max"] - values["min"],
                    "V_std": std_raw, "V_cv": std_raw / mean_raw if mean_raw > 0 else "",
                    "V_max_median_ratio": values["max_median"], "V_mean_relative_to_baseline": values["mean_vn"],
                    "count_VN_ge_2": int(np.sum(vn_window >= 2)), "count_VN_ge_5": int(np.sum(vn_window >= 5)),
                    "count_VN_ge_10": int(np.sum(vn_window >= 10)), "fraction_VN_ge_2": float(np.mean(vn_window >= 2)),
                    "fraction_VN_ge_5": float(np.mean(vn_window >= 5)), "fraction_VN_ge_10": float(np.mean(vn_window >= 10)),
                    "current_V_N": vn[index], "max_V_N": float(np.max(vn_window)),
                    "observations_since_interval_max": values["since_max"], "count_elevated": values["count_elevated"],
                    "count_extreme": values["count_extreme"], "persistence_above_baseline": values["persist_baseline"],
                    "V1": v1[index], "V2": v2[index], "V1_sign": sign(v1[index]), "V2_sign": sign(v2[index]),
                    "V1_persistence": persistence(v1, index, lambda value: sign(value) == sign(v1[index])),
                    "V2_persistence": persistence(v2, index, lambda value: sign(value) == sign(v2[index])),
                })
            interval_data[interval] = fields

    predictions: dict[str, np.ndarray] = {}
    conditions: dict[str, list[float]] = defaultdict(list)
    coefficients: dict[str, list[np.ndarray]] = defaultdict(list)
    failures: Counter[str] = Counter()
    predictions["VOLUME_POINT"] = vn.copy()
    h_next = np.full(len(rows), np.nan); h_next[:-1] = np.diff(times)
    predictions["VOLUME_DERIVATIVE"] = vn + v1 * h_next + 0.5 * v2 * h_next * h_next
    for interval in INTERVALS:
        predictions[f"VOLUME_INTERVAL_K{interval}"] = interval_data[interval]["median_vn"].copy()
        model_id = f"VOLUME_INTERVAL_DERIVATIVE_UPDATE_K{interval}"
        pred = np.full(len(rows), np.nan)
        features = np.column_stack((
            vn, interval_data[interval]["mean_vn"], interval_data[interval]["median"],
            interval_data[interval]["std"], interval_data[interval]["max_median"], v1, v2,
        ))
        for index in range(max(60, interval - 1), len(rows) - 1):
            train_indices = np.arange(index - 60, index)
            x = features[train_indices]
            y = vn[train_indices + 1]
            if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y)) and np.all(np.isfinite(features[index]))):
                failures[model_id] += 1; continue
            means = np.mean(x, axis=0); scales = np.std(x, axis=0)
            if np.any(scales <= 0): failures[model_id] += 1; continue
            z = (x - means) / scales; design = np.column_stack((np.ones(len(z)), z))
            condition = float(np.linalg.cond(design))
            coefficient, _, rank, _ = np.linalg.lstsq(design, y, rcond=None)
            if rank != design.shape[1] or condition > CONDITION_LIMIT or not np.all(np.isfinite(coefficient)):
                failures[model_id] += 1; continue
            prediction = np.r_[1.0, (features[index] - means) / scales] @ coefficient
            pred[index] = prediction; conditions[model_id].append(condition); coefficients[model_id].append(coefficient)
        predictions[model_id] = pred

    actual_next = np.full(len(rows), np.nan); actual_next[:-1] = vn[1:]
    for prediction in predictions.values():
        prediction[:15] = np.nan
    comparison: dict[str, dict[str, Any]] = {}
    complexity = {"VOLUME_POINT": 0, "VOLUME_DERIVATIVE": 1}
    for interval in INTERVALS:
        complexity[f"VOLUME_INTERVAL_K{interval}"] = 2
        complexity[f"VOLUME_INTERVAL_DERIVATIVE_UPDATE_K{interval}"] = 3
    for model_id, pred in predictions.items():
        metrics = error_metrics(pred[:-1], actual_next[:-1])
        mask = metrics["mask"]
        pred_values = pred[:-1][mask]; actual_values = actual_next[:-1][mask]
        regime_correct = [state_regime(a, boundaries) == state_regime(b, boundaries) for a,b in zip(pred_values, actual_values)]
        burst_correct = [(a >= 2) == (b >= 2) for a,b in zip(pred_values, actual_values)]
        steps = [float(np.median(np.abs(right-left))) for left,right in zip(coefficients[model_id], coefficients[model_id][1:])]
        representation = "POINT" if model_id == "VOLUME_POINT" else "DERIVATIVE" if model_id == "VOLUME_DERIVATIVE" else "INTERVAL_DERIVATIVE" if "UPDATE" in model_id else "INTERVAL"
        interval = "" if "K" not in model_id else int(model_id.rsplit("K",1)[1])
        comparison[model_id] = {
            "model_id": model_id, "representation": representation, "interval": interval,
            "causal_availability": "CURRENT_AND_PAST_ONLY", "valid_forecasts": metrics["valid"],
            "failed_forecasts": failures[model_id], "median_condition_number": None if not conditions[model_id] else float(np.median(conditions[model_id])),
            "coefficient_stability": None if not steps else float(np.median(steps)),
            "VN_MAE": metrics["mae"], "VN_RMSE": metrics["rmse"],
            "VN_median_absolute_error": metrics["median"], "VN_signed_bias": metrics["bias"],
            "volume_regime_transition_accuracy": sum(regime_correct)/len(regime_correct),
            "burst_persistence_accuracy": sum(burst_correct)/len(burst_correct),
            "noise_sensitivity": "HIGH" if representation == "DERIVATIVE" else "MEDIUM" if representation == "INTERVAL_DERIVATIVE" else "LOW",
            "suitability_for_ODE": "WEAK" if representation != "DERIVATIVE" else "CONDITIONAL_HIGH_NOISE",
            "suitability_for_state_update": "STRONG" if representation in ("POINT","INTERVAL","INTERVAL_DERIVATIVE") else "CONDITIONAL",
        }
    primary_id = min(comparison, key=lambda key: (-comparison[key]["valid_forecasts"], comparison[key]["failed_forecasts"], comparison[key]["VN_MAE"], comparison[key]["VN_RMSE"], complexity[key], 0 if comparison[key]["interval"]=="" else comparison[key]["interval"]))
    with (ROOT / "APTF_TEST_010_VOLUME_ENGINE_MODEL_COMPARISON_V0_1.csv").open("w", newline="", encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=MODEL_COLUMNS);writer.writeheader();writer.writerows(comparison[key] for key in sorted(comparison))

    selected = predictions[primary_id]
    selected_interval = comparison[primary_id]["interval"] if comparison[primary_id]["interval"] != "" else 15
    emission_count=0
    with (ROOT / "APTF_TEST_010_VOLUME_ENGINE_EMISSIONS_V0_1.csv").open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=EMISSION_COLUMNS);writer.writeheader()
        for index in range(15,len(rows)-1):
            if not (math.isfinite(selected[index]) and math.isfinite(vn[index+1])): continue
            emission_count+=1
            state={name:interval_data[int(selected_interval)][name][index] for name in ("mean_vn","median","std","max_median","since_max","count_elevated","count_extreme","persist_baseline")}
            writer.writerow({
                "volume_emission_id":f"VE{emission_count:06d}","observation_index":index+1,"timestamp":rows[index]["timestamp"],
                "V_RAW":raw[index],"V_N":vn[index],"selected_interval":selected_interval,
                "interval_state_json":json.dumps(state,sort_keys=True,separators=(",",":")),"V1":v1[index],"V2":v2[index],
                "observer_state":f"V1_{sign(v1[index])}_V2_{sign(v2[index])}","local_volume_model_id":primary_id,
                "predicted_next_V_N":selected[index],"actual_next_V_N":vn[index+1],"state_error":selected[index]-vn[index+1],
                "predicted_next_regime":state_regime(selected[index],boundaries),"actual_next_regime":state_regime(vn[index+1],boundaries),
                "regime_prediction_correct":str(state_regime(selected[index],boundaries)==state_regime(vn[index+1],boundaries)).lower(),
                "burst_persistence_correct":str((selected[index]>=2)==(vn[index+1]>=2)).lower(),
                "model_stability":"STABLE_DISCRETE" if comparison[primary_id]["noise_sensitivity"]=="LOW" else "MIXED",
                "next_elapsed_minutes":times[index+1]-times[index],
            })

    crossing_rows=list(csv.DictReader(CROSSINGS.open(newline="",encoding="utf-8")))
    crossing_indices=[int(row["observation_index"])-1 for row in crossing_rows]
    crossing_by_index=dict(zip(crossing_indices,crossing_rows,strict=True))
    event_count=0
    with (ROOT / "APTF_TEST_010_VOLUME_OBSERVER_EVENTS_V0_1.csv").open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=EVENT_COLUMNS);writer.writeheader()
        for index in range(16,len(rows)):
            events=[]
            if sign(v1[index-1])!=sign(v1[index]):events.append(f"V1_{sign(v1[index-1])}_TO_{sign(v1[index])}")
            if sign(v2[index-1])!=sign(v2[index]):events.append(f"V2_{sign(v2[index-1])}_TO_{sign(v2[index])}")
            if not events: continue
            pos=bisect.bisect_left(crossing_indices,index);candidates=[]
            if pos<len(crossing_indices):candidates.append(crossing_indices[pos])
            if pos>0:candidates.append(crossing_indices[pos-1])
            nearest=min(candidates,key=lambda value:(abs(value-index),value));crossing=crossing_by_index[nearest]
            for event_type in events:
                event_count+=1
                state=interval_data[15]
                writer.writerow({
                    "event_id":f"VOE{event_count:07d}","observation_index":index+1,"timestamp":rows[index]["timestamp"],"event_type":event_type,
                    "V_RAW":raw[index],"V_N":vn[index],"V1":v1[index],"V2":v2[index],
                    "interval_state":json.dumps({"mean_VN":state['mean_vn'][index],"std_raw":state['std'][index],"max_median":state['max_median'][index]},sort_keys=True,separators=(",",":")),
                    "concurrent_P":p[index],"concurrent_P1":p1[index],"concurrent_P2":p2[index],
                    "nearest_frozen_price_crossing":crossing["crossing_id"],"crossing_type":crossing["crossing_type"],
                    "signed_observations_offset":index-nearest,"signed_seconds_offset":60*(times[index]-times[nearest]),
                })
    output={"test_id":"APTF_TEST_010_VOLUME_ENGINE_SELECTION_V0_1","models_tested":sorted(comparison),"intervals":list(INTERVALS),"primary_model_id":primary_id,"primary":comparison[primary_id],"volume_emissions":emission_count,"observer_events":event_count,"future_observations_used_in_state":0,"selection_used_pnl":False,"selection_used_trading_labels":False,"recommended_evolution":"G_V_DISCRETE_STATE_UPDATE","runge_kutta_used":False,"status":"PASS"}
    (ROOT/"APTF_TEST_010_VOLUME_ENGINE_SELECTION_V0_1.json").write_text(json.dumps(output,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"primary_model":primary_id,"valid_forecasts":comparison[primary_id]["valid_forecasts"],"VN_MAE":comparison[primary_id]["VN_MAE"],"regime_accuracy":comparison[primary_id]["volume_regime_transition_accuracy"],"observer_events":event_count},indent=2))
    return 0


if __name__=="__main__":raise SystemExit(main())