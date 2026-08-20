from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np


ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"APTF_TEST_007_OBSERVATION_EPISODE_MAP_V0_1.csv"
MULTI=ROOT/"APTF_TEST_009V_PRICE_VOLUME_OBSERVATIONS_V0_1.csv"
VOLUME10=ROOT/"APTF_TEST_010_VOLUME_ENGINE_EMISSIONS_V0_1.csv"
VOLUME_INTERVAL10=ROOT/"APTF_TEST_010_VOLUME_INTERVAL_STATES_V0_1.csv"
VOLUME_EVENTS10=ROOT/"APTF_TEST_010_VOLUME_OBSERVER_EVENTS_V0_1.csv"
PRICE_PROJ=ROOT/"APTF_TEST_011_PRICE_RK45_PROJECTIONS_V0_1.csv"
PRICE_FAIL=ROOT/"APTF_TEST_011_RK45_SOLVER_FAILURES_V0_1.csv"
PRICE_INELIGIBLE=ROOT/"APTF_TEST_011_RK_INELIGIBLE_OBSERVATIONS_V0_1.csv"
SESSION10=ROOT/"APTF_TEST_010_SESSION_BOUNDARY_ANALYSIS_V0_1.csv"

VOLUME_COLUMNS=[
    "volume_observer_id","observation_index","timestamp","V_RAW","V_N","interval_state_15",
    "interval_state_status","V1","V2","V1_sign","V2_sign","V1_persistence",
    "V2_persistence","observer_event_state","burst_state","participation_condition_metrics",
    "G_V_predicted_next_V_N","actual_next_V_N","volume_update_error","volume_RK_executed",
]

CONTROL_COLUMNS=[
    "control_trajectory_id","observation_index","timestamp","price_rk_projection_reference",
    "price_projection_status","volume_observer_reference","price_projected_P1",
    "price_projected_P2","price_projected_J_P","price_projected_delta_P",
    "price_P1_distance_from_zero","price_projected_transition_flag","price_model_condition",
    "price_solver_nfev","volume_V_N","volume_interval_mean_VN","volume_interval_std_raw",
    "volume_burst_state","volume_observer_event_flag","concurrence_descriptor",
    "disagreement_descriptor","execution_window_open","frozen_position_state",
    "frozen_historical_emitter_decision","NO_NEW_TRADING_ACTION",
]

VOLUME_CONDITION_COLUMNS=[
    "volume_observer_id","observation_index","timestamp","V_N","interval_mean_VN",
    "interval_std_raw","interval_max_median_ratio","interval_count_elevated",
    "interval_count_extreme","persistence_above_baseline","V1","V2","V1_persistence",
    "V2_persistence","observer_event_count","burst_state","G_V_absolute_error",
]

GAP_COLUMNS=[
    "prior_session_id","next_session_id","prior_timestamp","next_timestamp","elapsed_gap_seconds",
    "prior_final_P","prior_final_P1","prior_final_P2","prior_final_V_N",
    "next_observed_P","next_observed_P1","next_observed_P2","next_observed_V_N",
    "RK_attempted_across_gap","RK_status","state_reset","reestimation_behavior",
]


def sgn(value:float)->int:return 1 if value>1e-15 else -1 if value<-1e-15 else 0
def persistence(values:list[float|None],index:int)->int:
    if values[index] is None:return 0
    target=sgn(values[index]);start=index
    while start-1>=0 and values[start-1] is not None and sgn(values[start-1])==target:start-=1
    return index-start+1

def parse_interval(text:str)->dict:
    if not text:return {}
    raw=json.loads(text)
    return {key:(None if isinstance(value,float) and not math.isfinite(value) else value) for key,value in raw.items()}

def main()->int:
    source=list(csv.DictReader(SOURCE.open(newline="",encoding="utf-8")))
    multi=list(csv.DictReader(MULTI.open(newline="",encoding="utf-8")))
    volume10={int(row["observation_index"]):row for row in csv.DictReader(VOLUME10.open(newline="",encoding="utf-8"))}
    interval15={int(row["observation_index"]):row for row in csv.DictReader(VOLUME_INTERVAL10.open(newline="",encoding="utf-8")) if row["interval"]=="15"}
    volume_events:dict[int,list[str]]=defaultdict(list)
    for row in csv.DictReader(VOLUME_EVENTS10.open(newline="",encoding="utf-8")):volume_events[int(row["observation_index"])].append(row["event_type"])
    projections={int(row["source_observation_index"]):row for row in csv.DictReader(PRICE_PROJ.open(newline="",encoding="utf-8"))}
    price_conditions={row["rk_projection_id"]:row for row in csv.DictReader(open(ROOT/"APTF_TEST_011_PRICE_CONDITION_METRICS_V0_1.csv",newline="",encoding="utf-8"))}
    failures={int(row["source_observation_index"]):row for row in csv.DictReader(PRICE_FAIL.open(newline="",encoding="utf-8"))}
    ineligible={int(row["source_observation_index"]):row for row in csv.DictReader(PRICE_INELIGIBLE.open(newline="",encoding="utf-8"))}
    v1=[None if row["V1"]=="" else float(row["V1"]) for row in multi];v2=[None if row["V2"]=="" else float(row["V2"]) for row in multi]

    volume_rows=[];volume_conditions=[]
    for index in range(15,len(source)):
        observation=index+1;emission=volume10.get(observation);interval_row=interval15.get(observation)
        interval={} if interval_row is None else {
            "mean_vn":float(interval_row["V_mean_relative_to_baseline"]),
            "median":float(interval_row["V_median"]),
            "std":float(interval_row["V_std"]),
            "max_median":float(interval_row["V_max_median_ratio"]),
            "since_max":int(interval_row["observations_since_interval_max"]),
            "count_elevated":int(interval_row["count_elevated"]),
            "count_extreme":int(interval_row["count_extreme"]),
            "persist_baseline":int(interval_row["persistence_above_baseline"]),
        }
        events=volume_events.get(observation,[]);vn=float(multi[index]["V_N"]);current_v1=v1[index];current_v2=v2[index]
        burst="EXTREME_BURST" if interval.get("count_extreme",0) not in (None,0) else "ELEVATED_ACTIVITY" if interval.get("count_elevated",0) not in (None,0) else "RELATIVE_BURST" if vn>=2 else "ORDINARY"
        predicted="" if emission is None else emission["predicted_next_V_N"];actual="" if emission is None else emission["actual_next_V_N"];error="" if emission is None else emission["state_error"]
        observer_id=f"VOBS{index-14:06d}"
        volume_rows.append({"volume_observer_id":observer_id,"observation_index":observation,"timestamp":source[index]["event_timestamp_utc"],"V_RAW":multi[index]["V_RAW"],"V_N":vn,"interval_state_15":json.dumps(interval,sort_keys=True,separators=(",",":")),"interval_state_status":"AVAILABLE" if interval and all(value is not None for value in interval.values()) else "INTERVAL_STATE_UNAVAILABLE_WARMUP","V1":"" if current_v1 is None else current_v1,"V2":"" if current_v2 is None else current_v2,"V1_sign":"" if current_v1 is None else sgn(current_v1),"V2_sign":"" if current_v2 is None else sgn(current_v2),"V1_persistence":persistence(v1,index),"V2_persistence":persistence(v2,index),"observer_event_state":"NONE" if not events else "|".join(events),"burst_state":burst,"participation_condition_metrics":json.dumps({"mean_vn":interval.get("mean_vn"),"std_raw":interval.get("std"),"max_median":interval.get("max_median"),"persistence":interval.get("persist_baseline")},sort_keys=True,separators=(",",":")),"G_V_predicted_next_V_N":predicted,"actual_next_V_N":actual,"volume_update_error":error,"volume_RK_executed":"false"})
        volume_conditions.append({"volume_observer_id":observer_id,"observation_index":observation,"timestamp":source[index]["event_timestamp_utc"],"V_N":vn,"interval_mean_VN":interval.get("mean_vn"),"interval_std_raw":interval.get("std"),"interval_max_median_ratio":interval.get("max_median"),"interval_count_elevated":interval.get("count_elevated"),"interval_count_extreme":interval.get("count_extreme"),"persistence_above_baseline":interval.get("persist_baseline"),"V1":"" if current_v1 is None else current_v1,"V2":"" if current_v2 is None else current_v2,"V1_persistence":persistence(v1,index),"V2_persistence":persistence(v2,index),"observer_event_count":len(events),"burst_state":burst,"G_V_absolute_error":"" if error=="" else abs(float(error))})
    with (ROOT/"APTF_TEST_011_VOLUME_OBSERVER_STATES_V0_1.csv").open("w",newline="",encoding="utf-8") as handle:writer=csv.DictWriter(handle,fieldnames=VOLUME_COLUMNS);writer.writeheader();writer.writerows(volume_rows)
    with (ROOT/"APTF_TEST_011_VOLUME_CONDITION_METRICS_V0_1.csv").open("w",newline="",encoding="utf-8") as handle:writer=csv.DictWriter(handle,fieldnames=VOLUME_CONDITION_COLUMNS);writer.writeheader();writer.writerows(volume_conditions)

    volume_by_observation={int(row["observation_index"]):row for row in volume_rows}
    control_rows=[];concurrence=Counter()
    for index in range(15,len(source)):
        observation=index+1;projection=projections.get(observation);volume=volume_by_observation[observation];events=volume_events.get(observation,[])
        if projection is not None:price_status="RK_SUCCESS"
        elif observation in failures:price_status="RK_SOLVER_FAILURE"
        else:price_status=f"RK_INELIGIBLE_{ineligible[observation]['reason']}"
        projected_transition=projection is not None and (projection["projected_upper_crossing"]=="True" or projection["projected_lower_crossing"]=="True")
        volume_changing=bool(events)
        if projection is None:descriptor="INCONCLUSIVE"
        elif projected_transition and volume_changing:descriptor="PRICE_PROJECTED_TRANSITION_VOLUME_CHANGING"
        elif projected_transition:descriptor="PRICE_PROJECTED_TRANSITION_VOLUME_STABLE"
        elif volume_changing:descriptor="PRICE_STABLE_VOLUME_CHANGING"
        else:descriptor="BOTH_STABLE"
        disagreement="INCONCLUSIVE" if projection is None else "PRICE_ONLY" if projected_transition and not volume_changing else "VOLUME_ONLY" if volume_changing and not projected_transition else "NONE"
        concurrence[descriptor]+=1
        control_rows.append({"control_trajectory_id":f"CT{index-14:06d}","observation_index":observation,"timestamp":source[index]["event_timestamp_utc"],"price_rk_projection_reference":"" if projection is None else projection["rk_projection_id"],"price_projection_status":price_status,"volume_observer_reference":volume["volume_observer_id"],"price_projected_P1":"" if projection is None else projection["projected_P1"],"price_projected_P2":"" if projection is None else projection["projected_P2"],"price_projected_J_P":"" if projection is None else price_conditions[projection["rk_projection_id"]]["projected_J_P_at_start"],"price_projected_delta_P":"" if projection is None else float(projection["projected_P"])-float(projection["current_P"]),"price_P1_distance_from_zero":"" if projection is None else abs(float(projection["projected_P1"])),"price_projected_transition_flag":"NONE" if not projected_transition else "UPPER" if projection["projected_upper_crossing"]=="True" else "LOWER","price_model_condition":"" if projection is None else projection["model_condition"],"price_solver_nfev":"" if projection is None else projection["nfev"],"volume_V_N":volume["V_N"],"volume_interval_mean_VN":json.loads(volume["participation_condition_metrics"])["mean_vn"],"volume_interval_std_raw":json.loads(volume["participation_condition_metrics"])["std_raw"],"volume_burst_state":volume["burst_state"],"volume_observer_event_flag":str(volume_changing).lower(),"concurrence_descriptor":descriptor,"disagreement_descriptor":disagreement,"execution_window_open":source[index]["is_regular_session"].lower(),"frozen_position_state":source[index]["test007_position_state_after"],"frozen_historical_emitter_decision":source[index]["position_decision"],"NO_NEW_TRADING_ACTION":"NO_NEW_TRADING_ACTION"})
    with (ROOT/"APTF_TEST_011_CONTROL_TRAJECTORY_OBSERVATIONS_V0_1.csv").open("w",newline="",encoding="utf-8") as handle:writer=csv.DictWriter(handle,fieldnames=CONTROL_COLUMNS);writer.writeheader();writer.writerows(control_rows)

    gaps=[]
    for observation,row in ineligible.items():
        if row["reason"]!="SESSION_BOUNDARY":continue
        index=observation-1;prior=index;next_index=index+1
        gaps.append({"prior_session_id":f"{source[prior]['event_timestamp_local'][:10]}:{source[prior]['session_type']}","next_session_id":f"{source[next_index]['event_timestamp_local'][:10]}:{source[next_index]['session_type']}","prior_timestamp":source[prior]["event_timestamp_utc"],"next_timestamp":source[next_index]["event_timestamp_utc"],"elapsed_gap_seconds":(datetime.fromisoformat(source[next_index]["event_timestamp_utc"].replace('Z','+00:00'))-datetime.fromisoformat(source[prior]["event_timestamp_utc"].replace('Z','+00:00'))).total_seconds(),"prior_final_P":multi[prior]["price"],"prior_final_P1":multi[prior]["frozen_P1"],"prior_final_P2":multi[prior]["frozen_P2"],"prior_final_V_N":multi[prior]["V_N"],"next_observed_P":multi[next_index]["price"],"next_observed_P1":multi[next_index]["frozen_P1"],"next_observed_P2":multi[next_index]["frozen_P2"],"next_observed_V_N":multi[next_index]["V_N"],"RK_attempted_across_gap":"false","RK_status":"RK_INELIGIBLE_SESSION_OR_TIME_GAP","state_reset":"false","reestimation_behavior":"WAIT_FOR_REAL_OBSERVATION_THEN_REESTIMATE"})
    with (ROOT/"APTF_TEST_011_SESSION_GAP_RK_AUDIT_V0_1.csv").open("w",newline="",encoding="utf-8") as handle:writer=csv.DictWriter(handle,fieldnames=GAP_COLUMNS);writer.writeheader();writer.writerows(gaps)

    # Enrich frozen Price summary with complete state confusion and precursor evidence.
    price_summary=json.loads((ROOT/"APTF_TEST_011_PRICE_RK45_SUMMARY_V0_1.json").read_text())
    projection_rows=list(projections.values());state_confusion=Counter((row["actual_derivative_state"],row["projected_derivative_state"]) for row in projection_rows)
    upper_actual=[row for row in projection_rows if row["actual_upper_crossing"]=="True"]
    lower_actual=[row for row in projection_rows if row["actual_lower_crossing"]=="True"]
    price_summary["derivative_state_confusion"]={f"{actual}->{projected}":count for (actual,projected),count in sorted(state_confusion.items())}
    price_summary["RK_D2_precursor_at_actual_upper"]={"actual_crossings":len(upper_actual),"projected_P1_positive_P2_negative":sum(float(row["projected_P1"])>0 and float(row["projected_P2"])<0 for row in upper_actual),"projected_upcoming_upper_crossing":sum(row["projected_upper_crossing"]=="True" for row in upper_actual)}
    price_summary["RK_D2_precursor_at_actual_lower"]={"actual_crossings":len(lower_actual),"projected_P1_negative_P2_positive":sum(float(row["projected_P1"])<0 and float(row["projected_P2"])>0 for row in lower_actual),"projected_upcoming_lower_crossing":sum(row["projected_lower_crossing"]=="True" for row in lower_actual)}
    price_summary["control_concurrence_counts"]=dict(concurrence);price_summary["volume_observer_rows"]=len(volume_rows);price_summary["volume_RK_executions"]=0;price_summary["session_gap_audit_rows"]=len(gaps)
    (ROOT/"APTF_TEST_011_PRICE_RK45_SUMMARY_V0_1.json").write_text(json.dumps(price_summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"volume_rows":len(volume_rows),"control_rows":len(control_rows),"concurrence":dict(concurrence),"session_gaps":len(gaps),"volume_RK":0},indent=2))
    return 0


if __name__=="__main__":raise SystemExit(main())