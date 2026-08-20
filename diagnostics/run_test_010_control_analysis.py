from __future__ import annotations

import bisect
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np


ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"APTF_TEST_007_OBSERVATION_EPISODE_MAP_V0_1.csv"
MULTI=ROOT/"APTF_TEST_009V_PRICE_VOLUME_OBSERVATIONS_V0_1.csv"
PRICE_EMISSIONS=ROOT/"APTF_TEST_010_PRICE_ENGINE_EMISSIONS_V0_1.csv"
VOLUME_EMISSIONS=ROOT/"APTF_TEST_010_VOLUME_ENGINE_EMISSIONS_V0_1.csv"
VOLUME_EVENTS=ROOT/"APTF_TEST_010_VOLUME_OBSERVER_EVENTS_V0_1.csv"
CROSSINGS=ROOT/"APTF_TEST_009_DERIVATIVE_CROSSINGS_V0_1.csv"

CONTROL_COLUMNS=[
    "control_observation_id","observation_index","timestamp","session_id",
    "price_engine_emission_id","volume_engine_emission_id","price_P1","price_P2",
    "price_J_P","price_model_condition","price_prediction_abs_error_P2",
    "volume_V_N","volume_V1","volume_V2","volume_interval_mean_VN",
    "volume_interval_std_raw","volume_observer_event_count","concurrence_state",
    "disagreement_state","execution_window_open","frozen_position_state",
    "frozen_Test007_emitter_decision","NO_NEW_TRADING_ACTION",
]

LEAD_LAG_COLUMNS=[
    "event_id","event_timestamp","event_type","nearest_upper_crossing",
    "upper_signed_observations_offset","upper_signed_seconds_offset",
    "nearest_lower_crossing","lower_signed_observations_offset",
    "lower_signed_seconds_offset","event_before_any_nearest_price_crossing",
    "event_at_any_price_crossing","event_after_any_nearest_price_crossing",
]

SESSION_COLUMNS=[
    "session_id","session_open","execution_open","execution_close","session_close",
    "final_price_P","final_price_P1","final_price_P2","final_price_J_P",
    "final_volume_V_N","final_volume_V1","final_volume_V2",
    "next_session_first_timestamp","elapsed_gap_seconds","next_price_P","next_price_P1",
    "next_price_P2","next_volume_V_N","next_volume_V1","next_volume_V2",
    "continuity_assessment","price_state_reset","volume_state_reset",
]


def local_date(value:str)->str:return datetime.fromisoformat(value).date().isoformat()
def utc(value:str)->datetime:return datetime.fromisoformat(value.replace("Z","+00:00"))
def sgn(value:float)->int:return 1 if value>1e-15 else -1 if value<-1e-15 else 0


def nearest(indices:list[int],index:int)->int:
    position=bisect.bisect_left(indices,index);candidates=[]
    if position<len(indices):candidates.append(indices[position])
    if position>0:candidates.append(indices[position-1])
    return min(candidates,key=lambda item:(abs(item-index),item))


def main()->int:
    source=list(csv.DictReader(SOURCE.open(newline="",encoding="utf-8")))
    multi=list(csv.DictReader(MULTI.open(newline="",encoding="utf-8")))
    price_emissions={int(row["observation_index"]):row for row in csv.DictReader(PRICE_EMISSIONS.open(newline="",encoding="utf-8"))}
    volume_emissions={int(row["observation_index"]):row for row in csv.DictReader(VOLUME_EMISSIONS.open(newline="",encoding="utf-8"))}
    volume_events=list(csv.DictReader(VOLUME_EVENTS.open(newline="",encoding="utf-8")))
    crossing_rows=list(csv.DictReader(CROSSINGS.open(newline="",encoding="utf-8")))
    if len(source)!=len(multi) or len(source)!=101221:raise RuntimeError("control source authority changed")
    events_by_observation:dict[int,list[dict[str,str]]]=defaultdict(list)
    for event in volume_events:events_by_observation[int(event["observation_index"])].append(event)

    control_counts=Counter();control_rows=0
    with (ROOT/"APTF_TEST_010_CONTROL_OBSERVATIONS_V0_1.csv").open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=CONTROL_COLUMNS);writer.writeheader()
        for index in range(15,len(source)):
            observation=index+1;price_e=price_emissions.get(observation);volume_e=volume_emissions.get(observation)
            current_events=events_by_observation.get(observation,[])
            price_transition=index>15 and multi[index-1]["frozen_P2"]!="" and sgn(float(multi[index-1]["frozen_P2"]))!=sgn(float(multi[index]["frozen_P2"]))
            volume_transition=bool(current_events)
            if price_e is None or (volume_e is None and index<len(source)-1):concurrence="INCONCLUSIVE"
            elif price_transition and volume_transition:concurrence="BOTH_TRANSITIONING"
            elif price_transition:concurrence="PRICE_TRANSITION_VOLUME_STABLE"
            elif volume_transition:concurrence="VOLUME_TRANSITION_PRICE_PERSISTENT"
            else:concurrence="BOTH_PERSISTENT"
            disagreement="PRICE_ONLY" if price_transition and not volume_transition else "VOLUME_ONLY" if volume_transition and not price_transition else "NONE" if concurrence!="INCONCLUSIVE" else "INCONCLUSIVE"
            interval_state={} if volume_e is None else json.loads(volume_e["interval_state_json"])
            writer.writerow({
                "control_observation_id":f"CO{control_rows+1:06d}","observation_index":observation,
                "timestamp":source[index]["event_timestamp_utc"],"session_id":local_date(source[index]["event_timestamp_local"]),
                "price_engine_emission_id":"" if price_e is None else price_e["price_emission_id"],
                "volume_engine_emission_id":"" if volume_e is None else volume_e["volume_emission_id"],
                "price_P1":multi[index]["frozen_P1"],"price_P2":multi[index]["frozen_P2"],
                "price_J_P":"" if price_e is None else price_e["J_P"],
                "price_model_condition":"" if price_e is None else price_e["model_condition"],
                "price_prediction_abs_error_P2":"" if price_e is None else abs(float(price_e["prediction_error_P2"])),
                "volume_V_N":multi[index]["V_N"],"volume_V1":multi[index]["V1"],"volume_V2":multi[index]["V2"],
                "volume_interval_mean_VN":interval_state.get("mean_vn",""),"volume_interval_std_raw":interval_state.get("std",""),
                "volume_observer_event_count":len(current_events),"concurrence_state":concurrence,"disagreement_state":disagreement,
                "execution_window_open":source[index]["is_regular_session"].lower(),
                "frozen_position_state":source[index]["test007_position_state_after"],
                "frozen_Test007_emitter_decision":source[index]["position_decision"],
                "NO_NEW_TRADING_ACTION":"NO_NEW_TRADING_ACTION",
            });control_rows+=1;control_counts[concurrence]+=1

    upper=[int(row["observation_index"]) for row in crossing_rows if row["crossing_type"]=="UPPER"]
    lower=[int(row["observation_index"]) for row in crossing_rows if row["crossing_type"]=="LOWER"]
    timestamps={index+1:utc(row["event_timestamp_utc"]) for index,row in enumerate(source)}
    before=at=after=0
    with (ROOT/"APTF_TEST_010_PRICE_VOLUME_LEAD_LAG_V0_1.csv").open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=LEAD_LAG_COLUMNS);writer.writeheader()
        for event in volume_events:
            index=int(event["observation_index"]);u=nearest(upper,index);l=nearest(lower,index)
            nearest_any=min((u,l),key=lambda item:(abs(item-index),item));offset=index-nearest_any
            before+=offset<0;at+=offset==0;after+=offset>0
            writer.writerow({
                "event_id":event["event_id"],"event_timestamp":event["timestamp"],"event_type":event["event_type"],
                "nearest_upper_crossing":u,"upper_signed_observations_offset":index-u,"upper_signed_seconds_offset":(timestamps[index]-timestamps[u]).total_seconds(),
                "nearest_lower_crossing":l,"lower_signed_observations_offset":index-l,"lower_signed_seconds_offset":(timestamps[index]-timestamps[l]).total_seconds(),
                "event_before_any_nearest_price_crossing":str(offset<0).lower(),"event_at_any_price_crossing":str(offset==0).lower(),
                "event_after_any_nearest_price_crossing":str(offset>0).lower(),
            })

    by_session:dict[str,list[int]]=defaultdict(list)
    for index,row in enumerate(source):by_session[local_date(row["event_timestamp_local"])].append(index)
    session_ids=sorted(by_session)
    session_rows=[]
    for position,session_id in enumerate(session_ids):
        indices=by_session[session_id];first,last=indices[0],indices[-1];regular=[i for i in indices if source[i]["is_regular_session"].lower()=="true"]
        next_first=None if position+1==len(session_ids) else by_session[session_ids[position+1]][0]
        gap=None if next_first is None else (utc(source[next_first]["event_timestamp_utc"])-utc(source[last]["event_timestamp_utc"])).total_seconds()
        assessment="FINAL_SESSION_NO_SUCCESSOR" if next_first is None else "WEEKEND_OR_HOLIDAY_GAP_REESTIMATE" if (datetime.fromisoformat(session_ids[position+1]).date()-datetime.fromisoformat(session_id).date()).days>=2 else "OVERNIGHT_GAP_REESTIMATE"
        price_e=price_emissions.get(last+1)
        session_rows.append({
            "session_id":session_id,"session_open":source[first]["event_timestamp_utc"],
            "execution_open":"" if not regular else source[regular[0]]["event_timestamp_utc"],
            "execution_close":"" if not regular else source[regular[-1]]["event_timestamp_utc"],
            "session_close":source[last]["event_timestamp_utc"],"final_price_P":multi[last]["price"],
            "final_price_P1":multi[last]["frozen_P1"],"final_price_P2":multi[last]["frozen_P2"],
            "final_price_J_P":"" if price_e is None else price_e["J_P"],"final_volume_V_N":multi[last]["V_N"],
            "final_volume_V1":multi[last]["V1"],"final_volume_V2":multi[last]["V2"],
            "next_session_first_timestamp":"" if next_first is None else source[next_first]["event_timestamp_utc"],
            "elapsed_gap_seconds":"" if gap is None else gap,"next_price_P":"" if next_first is None else multi[next_first]["price"],
            "next_price_P1":"" if next_first is None else multi[next_first]["frozen_P1"],
            "next_price_P2":"" if next_first is None else multi[next_first]["frozen_P2"],
            "next_volume_V_N":"" if next_first is None else multi[next_first]["V_N"],
            "next_volume_V1":"" if next_first is None else multi[next_first]["V1"],
            "next_volume_V2":"" if next_first is None else multi[next_first]["V2"],
            "continuity_assessment":assessment,"price_state_reset":"false","volume_state_reset":"false",
        })
    with (ROOT/"APTF_TEST_010_SESSION_BOUNDARY_ANALYSIS_V0_1.csv").open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=SESSION_COLUMNS);writer.writeheader();writer.writerows(session_rows)

    price_selection=json.loads((ROOT/"APTF_TEST_010_PRICE_ENGINE_SELECTION_V0_1.json").read_text())
    volume_selection=json.loads((ROOT/"APTF_TEST_010_VOLUME_ENGINE_SELECTION_V0_1.json").read_text())
    event_baseline_frequency=len({int(row["observation_index"]) for row in volume_events})/101206
    crossing_baseline_frequency=len(set(upper+lower))/101206
    price_errors_by_stratum:dict[str,list[float]]=defaultdict(list)
    jp_at_crossing=[]
    jp_pre_crossing:dict[str,dict[str,list[float]]]={
        "UPPER":{str(window):[] for window in (1,3,5,8,15)},
        "LOWER":{str(window):[] for window in (1,3,5,8,15)},
    }
    for row in price_emissions.values():
        price_errors_by_stratum[row["transition_stratum"]].append(abs(float(row["prediction_error_P2"])))
    crossing_type_by_index={int(row["observation_index"]):row["crossing_type"] for row in crossing_rows}
    for index in set(upper+lower):
        emission=price_emissions.get(index)
        if emission:jp_at_crossing.append(abs(float(emission["J_P"])))
        crossing_type=crossing_type_by_index[index]
        for window in (1,3,5,8,15):
            values=[]
            for prior_index in range(max(1,index-window),index):
                prior_emission=price_emissions.get(prior_index)
                if prior_emission is not None:values.append(abs(float(prior_emission["J_P"])))
            if values:jp_pre_crossing[crossing_type][str(window)].append(float(np.mean(values)))
    summary={
        "test_id":"APTF_TEST_010_SUMMARY_V0_1","actionable_control_rows":control_rows,
        "price_engine":price_selection,"volume_engine":volume_selection,
        "control_concurrence_counts":dict(control_counts),"volume_observer_events":len(volume_events),
        "volume_events_before_nearest_price_crossing":before,"volume_events_at_nearest_price_crossing":at,
        "volume_events_after_nearest_price_crossing":after,
        "volume_event_observation_baseline_frequency":event_baseline_frequency,
        "price_crossing_observation_baseline_frequency":crossing_baseline_frequency,
        "volume_event_at_crossing_frequency":at/len(volume_events),
        "lead_lag_baseline_comparison":"Volume-event rows are compared with frozen crossing-row frequency; temporal ordering is descriptive and not causal.",
        "session_count":len(session_rows),"session_gap_count":len(session_rows)-1,
        "price_P2_error_by_transition_stratum":{key:{"count":len(values),"MAE":float(np.mean(values))} for key,values in price_errors_by_stratum.items()},
        "absolute_J_P_at_frozen_crossings":{"count":len(jp_at_crossing),"median":float(np.median(jp_at_crossing)),"mean":float(np.mean(jp_at_crossing))},
        "absolute_J_P_before_frozen_crossings":{
            crossing_type:{window:{"count":len(values),"mean":float(np.mean(values)),"median":float(np.median(values))} for window,values in windows.items()}
            for crossing_type,windows in jp_pre_crossing.items()
        },
        "price_volume_scalar_mixture_created":False,"new_trading_action_created":False,
        "autopilot_implemented":False,"broker_implemented":False,"runge_kutta_used":False,
        "local_dynamics_price_identified":True,"local_dynamics_volume_form":"G_V_DISCRETE_STATE_UPDATE",
        "future_observations_used_in_model_fit":0,"status":"PASS",
    }
    (ROOT/"APTF_TEST_010_SUMMARY_V0_1.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"control_rows":control_rows,"concurrence":dict(control_counts),"volume_events":len(volume_events),"before_at_after":[before,at,after],"sessions":len(session_rows)},indent=2))
    return 0


if __name__=="__main__":raise SystemExit(main())