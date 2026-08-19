# APTF Two-Row Interface Payload Audit V0.1

Status: **DIAGNOSTIC FAIL - full zero-mock chain is not executable past D02**  
Authority status: all four frozen authority hashes verified  
Implementation changes: **NONE**  
Freeze changes: **NONE**  
Replay CSV regenerated: **NO**  
Position controller invoked: **NO**

## Executive finding

The real historical rows propagate changing information through the real frozen D01 and D02 implementations. D01 receives changing close and volume, emits changing DMO/FMO payloads, and D02 emits materially different `ReturnShape` payloads. Both shapes have `path_direction=UPWARD`.

No information collapse is observed through D02. The zero-mock trace stops at `D02 ReturnShape -> D04 TradingEnvelope.process`: D04 requires an `EnvelopeContext` whose 11 non-observational market/capital/portfolio/execution values are hard-coded by the replay as perfect conditions. Those values are not in the historical source. Invoking D04 with them would violate the absolute zero-mock rule. D03 is consequently not invoked; independently, D03 requires a real position/control context that this diagnostic explicitly forbids fabricating.

The prior six-month CSV contains `FLAT` for both target rows, but those values are excluded from this zero-mock trace because that replay used the synthetic context documented below. This audit therefore does **not** establish the cause of those two D03 results.

## Frozen authorities

| Component | Authority artifact | SHA256 | Status |
|---|---|---|---|
| D01 | `D01_PRE_STAGE_3_ARCHITECTURE_FREEZE_V0_1.json` | `b6ed942e41ec1c72350cf9247597e5819a942dbe9d04770c23e243204165b235` | VERIFIED |
| D02 | `D02_RETURNSHAPE_IMPLEMENTATION_V0_2_FREEZE.json` | `c8029c4b9608547bbf7960f05e4f8613480c4fb2bf8594d94482516b954f7e72` | VERIFIED |
| D03 | `D03_DECISION_CONTROL_IMPLEMENTATION_V0_1_FREEZE.json` | `6a93291ffe555a3fff1239a9a4f88c0a1546b6c46a02b60586614b60a3c91ad6` | VERIFIED |
| D04 | `D04_TRADING_ENVELOPE_IMPLEMENTATION_V0_2_1_FREEZE.json` | `f72a86b3085bd11d8626f06f1fe3faedde60570365488176011239382a46f1af` | VERIFIED |

## Exact runtime call chain

| Stage | Module | Class / function |
|---|---|---|
| Source mapping | `position_transition_controller.real_causal_replay_harness_v0_2` | `RealCausalReplayHarness.source_row_to_normalized_observation` |
| D01 | `d01.v02.model` | `D01V02Model.step` |
| D02 | `d02.v02.builder` | `build_return_shape` |
| D04 | `aptf_d04.envelope.trading_envelope` | `TradingEnvelope.process` (not invoked in zero-mock trace) |
| D03 | `d03.v01` | `evaluate_decision` (not invoked in zero-mock trace) |

## Historical rows

The authoritative source is `data/market/normalized/SPY_1min_normalized_v0_1.csv` (SHA256 `73957227a0cc09103f7ca5ff62b011edd7c80c220017d91fb97c5fb5e6a1055d`). Row A is zero-based row 16/source row 17; Row B is zero-based row 17/source row 18.

### Row A complete source record

```json
{
  "close": "366.0",
  "close_return_1m": "0.0005193953145075092",
  "data_valid": "true",
  "entity_id": "SPY",
  "event_timestamp_local": "2022-09-30T04:16:00-04:00",
  "event_timestamp_utc": "2022-09-30T08:16:00Z",
  "high": "366.0",
  "high_low_range": "0.0",
  "high_low_range_fraction": "0.0",
  "is_regular_session": "false",
  "low": "366.0",
  "minute_of_session": "-1",
  "open": "366.0",
  "open_close_change": "0.0",
  "open_close_return": "0.0",
  "quality_flags": "",
  "session_type": "PREMARKET",
  "source_dataset": "SPY_1min_firstratedata",
  "source_provider": "FirstRateData",
  "source_row_number": "17",
  "timezone": "America/New_York",
  "volume": "616.0"
}
```

### Row B complete source record

```json
{
  "close": "366.17",
  "close_return_1m": "0.00046448087431705254",
  "data_valid": "true",
  "entity_id": "SPY",
  "event_timestamp_local": "2022-09-30T04:17:00-04:00",
  "event_timestamp_utc": "2022-09-30T08:17:00Z",
  "high": "366.2",
  "high_low_range": "0.13999999999998636",
  "high_low_range_fraction": "0.0003823360734084888",
  "is_regular_session": "false",
  "low": "366.06",
  "minute_of_session": "-1",
  "open": "366.06",
  "open_close_change": "0.11000000000001364",
  "open_close_return": "0.0003004971862536898",
  "quality_flags": "",
  "session_type": "PREMARKET",
  "source_dataset": "SPY_1min_firstratedata",
  "source_provider": "FirstRateData",
  "source_row_number": "18",
  "timezone": "America/New_York",
  "volume": "2398.0"
}
```

## Source -> D01 contract

Runtime type: `d01.v02.observations.NormalizedObservation`

| Field | Type | Exact source | Origin classification |
|---|---|---|---|
| `entity_id` | `str` | SPY harness configuration | CONFIGURATION |
| `event_time` | `float` | event_timestamp_utc parsed to epoch seconds | CURRENT SOURCE ROW / DERIVED CAUSALLY |
| `receive_time` | `float` | event_time copied because source has no receive timestamp | REQUIRED AUTHORITATIVE ADAPTER VALUE |
| `sequence_id` | `int` | zero-based CSV row index | DERIVED CAUSALLY |
| `price` | `float` | source close | CURRENT SOURCE ROW |
| `volume` | `float` | source volume | CURRENT SOURCE ROW |
| `bid` | `float | None` | None; source has no bid | OTHER: source field unavailable |
| `ask` | `float | None` | None; source has no ask | OTHER: source field unavailable |
| `bid_size` | `float | None` | dataclass default None | DEFAULT VALUE |
| `ask_size` | `float | None` | dataclass default None | DEFAULT VALUE |
| `session` | `str` | source session_type | CURRENT SOURCE ROW |
| `source_quality` | `float` | 1.0 when source data_valid=true, else 0.5 | DERIVED CAUSALLY |
| `availability_mask` | `dict[str,bool] | None` | {"price": true, "volume": true} | REQUIRED AUTHORITATIVE ADAPTER VALUE |

OHLCV consumption:

| Source field | Consumed by D01 | Mapping |
|---|---|---|
| open | NO | Does not enter D01 |
| high | NO | Does not enter D01 |
| low | NO | Does not enter D01 |
| close | YES | `close -> NormalizedObservation.price` |
| volume | YES | `volume -> NormalizedObservation.volume`; frozen default enables the volume channel |

## Complete Row A D01 payload

### Input

```json
{
  "ask": null,
  "ask_size": null,
  "availability_mask": {
    "price": true,
    "volume": true
  },
  "bid": null,
  "bid_size": null,
  "entity_id": "SPY",
  "event_time": 1664525760.0,
  "price": 366.0,
  "receive_time": 1664525760.0,
  "sequence_id": 16,
  "session": "PREMARKET",
  "source_quality": 1.0,
  "volume": 616.0
}
```

### Output: DMOOutput and FMOOutput

```json
{
  "dmo": {
    "coherence": 0.9999999907876206,
    "config_hash": "30DE0D125752D222FED57D80581C73939C4C0BA9ABD5F6FDAA9CFCB9970BF8DD",
    "data_quality": 1.0,
    "dmo_schema_version": "0.2.0",
    "entity_id": "SPY",
    "fmo_schema_version": "0.2.0",
    "forward_half_life": 15.0,
    "model_health": "DEGRADED_DATA",
    "model_time": 1664525760.0,
    "model_version": "0.2",
    "observation_half_life": 15.0,
    "parameter_state": {
      "ref_alpha": 0.051562086467087535
    },
    "parameter_update_magnitude": {
      "ref_alpha": 0.00014554768354110847
    },
    "persistence": 0.6840391573948615,
    "perturbation_class": "REVERSING",
    "perturbation_magnitude": 0.027385217798428497,
    "reversal_propensity": 0.5091154115712131,
    "state_acceleration": 6.0582676702565786e-05,
    "state_curvature": 6.0580182036429116e-05,
    "state_hash": "FCCB692875A5CF82F914D2E27640C3A503998D00968F9A711E439589AD9BEC03",
    "state_level": 0.1861982523830909,
    "state_support_ratio": 0.6827851084628193,
    "state_velocity": 0.005239547828088794,
    "strength": 0.8043937518637954,
    "trace_id": "SPY:17",
    "uncertainty": 0.296755743816712
  },
  "fmo": {
    "entity_id": "SPY",
    "interval_length": 67.3155665570578,
    "model_time": 1664525760.0,
    "samples": [
      {
        "level": 0.19462833422987413,
        "persistence": 0.635457786134345,
        "reversal_propensity": 0.5162175446487312,
        "strength": 0.7472646371391879,
        "tau": 1.594239365852591,
        "uncertainty": 0.30740894343298913,
        "velocity": 0.0048674281686777185
      },
      {
        "level": 0.21621895429655258,
        "persistence": 0.5292617228701793,
        "reversal_propensity": 0.5317423961307151,
        "strength": 0.6223837018319762,
        "tau": 5.551463911887316,
        "uncertainty": 0.3306962206559649,
        "velocity": 0.004053996150039425
      },
      {
        "level": 0.25056511169068635,
        "persistence": 0.40172871716234093,
        "reversal_propensity": 0.5503865050723059,
        "strength": 0.47241165441514005,
        "tau": 11.517859785277338,
        "uncertainty": 0.35866238406835116,
        "velocity": 0.0030771291449237913
      },
      {
        "level": 0.2988055001269704,
        "persistence": 0.27998008997850254,
        "reversal_propensity": 0.5681849930488588,
        "strength": 0.3292417292055194,
        "tau": 19.33132014244643,
        "uncertainty": 0.38536011603318054,
        "velocity": 0.002144568854715667
      },
      {
        "level": 0.3628285929114741,
        "persistence": 0.18003679591315763,
        "reversal_propensity": 0.5827957493169613,
        "strength": 0.21171371868485547,
        "tau": 28.88680678510959,
        "uncertainty": 0.4072762504353342,
        "velocity": 0.001379031292002958
      },
      {
        "level": 0.4450705464748999,
        "persistence": 0.10719550621243867,
        "reversal_propensity": 0.5934444510635297,
        "strength": 0.12605622718084775,
        "tau": 40.10751729615585,
        "uncertainty": 0.42324930305518693,
        "velocity": 0.0008210874709209755
      },
      {
        "level": 0.5484202090992059,
        "persistence": 0.05926219098192461,
        "reversal_propensity": 0.6004518445310421,
        "strength": 0.06968919195966662,
        "tau": 52.93342565084451,
        "uncertainty": 0.4337603932564555,
        "velocity": 0.00045393173868829594
      },
      {
        "level": 0.6761631143414789,
        "persistence": 0.030489290348908064,
        "reversal_propensity": 0.6046581681489176,
        "strength": 0.03585378759430505,
        "tau": 67.3155665570578,
        "uncertainty": 0.44006987868326874,
        "velocity": 0.0002335394009255148
      }
    ]
  }
}
```

## Complete Row B D01 payload

### Input

```json
{
  "ask": null,
  "ask_size": null,
  "availability_mask": {
    "price": true,
    "volume": true
  },
  "bid": null,
  "bid_size": null,
  "entity_id": "SPY",
  "event_time": 1664525820.0,
  "price": 366.17,
  "receive_time": 1664525820.0,
  "sequence_id": 17,
  "session": "PREMARKET",
  "source_quality": 1.0,
  "volume": 2398.0
}
```

### Output: DMOOutput and FMOOutput

```json
{
  "dmo": {
    "coherence": 0.9999931783150069,
    "config_hash": "30DE0D125752D222FED57D80581C73939C4C0BA9ABD5F6FDAA9CFCB9970BF8DD",
    "data_quality": 1.0,
    "dmo_schema_version": "0.2.0",
    "entity_id": "SPY",
    "fmo_schema_version": "0.2.0",
    "forward_half_life": 15.0,
    "model_health": "DEGRADED_DATA",
    "model_time": 1664525820.0,
    "model_version": "0.2",
    "observation_half_life": 15.0,
    "parameter_state": {
      "ref_alpha": 0.05176646431379669
    },
    "parameter_update_magnitude": {
      "ref_alpha": 0.00020437784670915282
    },
    "persistence": 0.6672308993184185,
    "perturbation_class": "CONTRADICTING",
    "perturbation_magnitude": 0.003949663883064501,
    "reversal_propensity": 0.7484880373502629,
    "state_acceleration": -8.532022211364249e-06,
    "state_curvature": -8.531736177522575e-06,
    "state_hash": "0237A5C4ABA304EB7C9D5B1BFC651A080250A381B0E655D402EFBC6790B95509",
    "state_level": 0.4698558421496643,
    "state_support_ratio": 0.5864884257246546,
    "state_velocity": 0.004727626495321619,
    "strength": 0.8976642163450754,
    "trace_id": "SPY:18",
    "uncertainty": 0.2727585484077373
  },
  "fmo": {
    "entity_id": "SPY",
    "interval_length": 72.006895138787,
    "model_time": 1664525820.0,
    "samples": [
      {
        "level": 0.4779056672740783,
        "persistence": 0.6166690634559729,
        "reversal_propensity": 0.7560658992139888,
        "strength": 0.8296404620303484,
        "tau": 1.7053444353880702,
        "uncertainty": 0.28412534120332605,
        "velocity": 0.004369373490073243
      },
      {
        "level": 0.49777972613807386,
        "persistence": 0.5071089788286183,
        "reversal_propensity": 0.772486014760087,
        "strength": 0.6822429604905098,
        "tau": 5.938354235363982,
        "uncertainty": 0.3087555145224734,
        "velocity": 0.0035930917569534787
      },
      {
        "level": 0.527455273135219,
        "persistence": 0.37758869942444917,
        "reversal_propensity": 0.7918976276719703,
        "strength": 0.5079918575651131,
        "tau": 12.320557698622846,
        "uncertainty": 0.3378729338902984,
        "velocity": 0.0026753832017620115
      },
      {
        "level": 0.5657921485680542,
        "persistence": 0.25661687918335097,
        "reversal_propensity": 0.8100280560386229,
        "strength": 0.3452414898475953,
        "tau": 20.678550498592156,
        "uncertainty": 0.36506857644027735,
        "velocity": 0.0018182442665848337
      },
      {
        "level": 0.6118661554346266,
        "persistence": 0.1600128563323852,
        "reversal_propensity": 0.8245064057298089,
        "strength": 0.21527452555251092,
        "tau": 30.89997415837988,
        "uncertainty": 0.38678610097705635,
        "velocity": 0.0011337619704990091
      },
      {
        "level": 0.6648314712296783,
        "persistence": 0.09189178830503945,
        "reversal_propensity": 0.8347159251176148,
        "strength": 0.12362732334736433,
        "tau": 42.90267377863407,
        "uncertainty": 0.4021003800587652,
        "velocity": 0.0006510940268760986
      },
      {
        "level": 0.7238683285913438,
        "persistence": 0.04874603453262663,
        "reversal_propensity": 0.8411823153607056,
        "strength": 0.06558085204590938,
        "tau": 56.62244002576115,
        "uncertainty": 0.41179996542340136,
        "velocity": 0.00034538724845284863
      },
      {
        "level": 0.7881583099566002,
        "persistence": 0.02394383961392316,
        "reversal_propensity": 0.8448994985643071,
        "strength": 0.03221302857118924,
        "tau": 72.006895138787,
        "uncertainty": 0.4173757402288036,
        "velocity": 0.0001696527104397393
      }
    ]
  }
}
```

## D01 field-level differences

Input: 5 changed, 9 same, 0 not present.

| Field | Row A | Row B | Classification |
|---|---:|---:|---|
| `ask` | `null` | `null` | SAME |
| `ask_size` | `null` | `null` | SAME |
| `availability_mask.price` | `true` | `true` | SAME |
| `availability_mask.volume` | `true` | `true` | SAME |
| `bid` | `null` | `null` | SAME |
| `bid_size` | `null` | `null` | SAME |
| `entity_id` | `"SPY"` | `"SPY"` | SAME |
| `event_time` | `1664525760.0` | `1664525820.0` | CHANGED |
| `price` | `366.0` | `366.17` | CHANGED |
| `receive_time` | `1664525760.0` | `1664525820.0` | CHANGED |
| `sequence_id` | `16` | `17` | CHANGED |
| `session` | `"PREMARKET"` | `"PREMARKET"` | SAME |
| `source_quality` | `1.0` | `1.0` | SAME |
| `volume` | `616.0` | `2398.0` | CHANGED |

The complete 85-field flattened D01 output diff is in `APTF_TWO_ROW_DIRECTION_PROPAGATION_TRACE_V0_1.json` under `diffs.d01_output`: 75 changed and 10 same.

## Complete D01 -> D02 payloads

D02 receives the exact pair `(DMOOutput, FMOOutput)` returned by D01. No adapter, window, or accumulated D02 state exists. D02 is invoked once per valid D01 step.

### Row A D02 input

```json
{
  "dmo": {
    "coherence": 0.9999999907876206,
    "config_hash": "30DE0D125752D222FED57D80581C73939C4C0BA9ABD5F6FDAA9CFCB9970BF8DD",
    "data_quality": 1.0,
    "dmo_schema_version": "0.2.0",
    "entity_id": "SPY",
    "fmo_schema_version": "0.2.0",
    "forward_half_life": 15.0,
    "model_health": "DEGRADED_DATA",
    "model_time": 1664525760.0,
    "model_version": "0.2",
    "observation_half_life": 15.0,
    "parameter_state": {
      "ref_alpha": 0.051562086467087535
    },
    "parameter_update_magnitude": {
      "ref_alpha": 0.00014554768354110847
    },
    "persistence": 0.6840391573948615,
    "perturbation_class": "REVERSING",
    "perturbation_magnitude": 0.027385217798428497,
    "reversal_propensity": 0.5091154115712131,
    "state_acceleration": 6.0582676702565786e-05,
    "state_curvature": 6.0580182036429116e-05,
    "state_hash": "FCCB692875A5CF82F914D2E27640C3A503998D00968F9A711E439589AD9BEC03",
    "state_level": 0.1861982523830909,
    "state_support_ratio": 0.6827851084628193,
    "state_velocity": 0.005239547828088794,
    "strength": 0.8043937518637954,
    "trace_id": "SPY:17",
    "uncertainty": 0.296755743816712
  },
  "fmo": {
    "entity_id": "SPY",
    "interval_length": 67.3155665570578,
    "model_time": 1664525760.0,
    "samples": [
      {
        "level": 0.19462833422987413,
        "persistence": 0.635457786134345,
        "reversal_propensity": 0.5162175446487312,
        "strength": 0.7472646371391879,
        "tau": 1.594239365852591,
        "uncertainty": 0.30740894343298913,
        "velocity": 0.0048674281686777185
      },
      {
        "level": 0.21621895429655258,
        "persistence": 0.5292617228701793,
        "reversal_propensity": 0.5317423961307151,
        "strength": 0.6223837018319762,
        "tau": 5.551463911887316,
        "uncertainty": 0.3306962206559649,
        "velocity": 0.004053996150039425
      },
      {
        "level": 0.25056511169068635,
        "persistence": 0.40172871716234093,
        "reversal_propensity": 0.5503865050723059,
        "strength": 0.47241165441514005,
        "tau": 11.517859785277338,
        "uncertainty": 0.35866238406835116,
        "velocity": 0.0030771291449237913
      },
      {
        "level": 0.2988055001269704,
        "persistence": 0.27998008997850254,
        "reversal_propensity": 0.5681849930488588,
        "strength": 0.3292417292055194,
        "tau": 19.33132014244643,
        "uncertainty": 0.38536011603318054,
        "velocity": 0.002144568854715667
      },
      {
        "level": 0.3628285929114741,
        "persistence": 0.18003679591315763,
        "reversal_propensity": 0.5827957493169613,
        "strength": 0.21171371868485547,
        "tau": 28.88680678510959,
        "uncertainty": 0.4072762504353342,
        "velocity": 0.001379031292002958
      },
      {
        "level": 0.4450705464748999,
        "persistence": 0.10719550621243867,
        "reversal_propensity": 0.5934444510635297,
        "strength": 0.12605622718084775,
        "tau": 40.10751729615585,
        "uncertainty": 0.42324930305518693,
        "velocity": 0.0008210874709209755
      },
      {
        "level": 0.5484202090992059,
        "persistence": 0.05926219098192461,
        "reversal_propensity": 0.6004518445310421,
        "strength": 0.06968919195966662,
        "tau": 52.93342565084451,
        "uncertainty": 0.4337603932564555,
        "velocity": 0.00045393173868829594
      },
      {
        "level": 0.6761631143414789,
        "persistence": 0.030489290348908064,
        "reversal_propensity": 0.6046581681489176,
        "strength": 0.03585378759430505,
        "tau": 67.3155665570578,
        "uncertainty": 0.44006987868326874,
        "velocity": 0.0002335394009255148
      }
    ]
  }
}
```

### Row B D02 input

```json
{
  "dmo": {
    "coherence": 0.9999931783150069,
    "config_hash": "30DE0D125752D222FED57D80581C73939C4C0BA9ABD5F6FDAA9CFCB9970BF8DD",
    "data_quality": 1.0,
    "dmo_schema_version": "0.2.0",
    "entity_id": "SPY",
    "fmo_schema_version": "0.2.0",
    "forward_half_life": 15.0,
    "model_health": "DEGRADED_DATA",
    "model_time": 1664525820.0,
    "model_version": "0.2",
    "observation_half_life": 15.0,
    "parameter_state": {
      "ref_alpha": 0.05176646431379669
    },
    "parameter_update_magnitude": {
      "ref_alpha": 0.00020437784670915282
    },
    "persistence": 0.6672308993184185,
    "perturbation_class": "CONTRADICTING",
    "perturbation_magnitude": 0.003949663883064501,
    "reversal_propensity": 0.7484880373502629,
    "state_acceleration": -8.532022211364249e-06,
    "state_curvature": -8.531736177522575e-06,
    "state_hash": "0237A5C4ABA304EB7C9D5B1BFC651A080250A381B0E655D402EFBC6790B95509",
    "state_level": 0.4698558421496643,
    "state_support_ratio": 0.5864884257246546,
    "state_velocity": 0.004727626495321619,
    "strength": 0.8976642163450754,
    "trace_id": "SPY:18",
    "uncertainty": 0.2727585484077373
  },
  "fmo": {
    "entity_id": "SPY",
    "interval_length": 72.006895138787,
    "model_time": 1664525820.0,
    "samples": [
      {
        "level": 0.4779056672740783,
        "persistence": 0.6166690634559729,
        "reversal_propensity": 0.7560658992139888,
        "strength": 0.8296404620303484,
        "tau": 1.7053444353880702,
        "uncertainty": 0.28412534120332605,
        "velocity": 0.004369373490073243
      },
      {
        "level": 0.49777972613807386,
        "persistence": 0.5071089788286183,
        "reversal_propensity": 0.772486014760087,
        "strength": 0.6822429604905098,
        "tau": 5.938354235363982,
        "uncertainty": 0.3087555145224734,
        "velocity": 0.0035930917569534787
      },
      {
        "level": 0.527455273135219,
        "persistence": 0.37758869942444917,
        "reversal_propensity": 0.7918976276719703,
        "strength": 0.5079918575651131,
        "tau": 12.320557698622846,
        "uncertainty": 0.3378729338902984,
        "velocity": 0.0026753832017620115
      },
      {
        "level": 0.5657921485680542,
        "persistence": 0.25661687918335097,
        "reversal_propensity": 0.8100280560386229,
        "strength": 0.3452414898475953,
        "tau": 20.678550498592156,
        "uncertainty": 0.36506857644027735,
        "velocity": 0.0018182442665848337
      },
      {
        "level": 0.6118661554346266,
        "persistence": 0.1600128563323852,
        "reversal_propensity": 0.8245064057298089,
        "strength": 0.21527452555251092,
        "tau": 30.89997415837988,
        "uncertainty": 0.38678610097705635,
        "velocity": 0.0011337619704990091
      },
      {
        "level": 0.6648314712296783,
        "persistence": 0.09189178830503945,
        "reversal_propensity": 0.8347159251176148,
        "strength": 0.12362732334736433,
        "tau": 42.90267377863407,
        "uncertainty": 0.4021003800587652,
        "velocity": 0.0006510940268760986
      },
      {
        "level": 0.7238683285913438,
        "persistence": 0.04874603453262663,
        "reversal_propensity": 0.8411823153607056,
        "strength": 0.06558085204590938,
        "tau": 56.62244002576115,
        "uncertainty": 0.41179996542340136,
        "velocity": 0.00034538724845284863
      },
      {
        "level": 0.7881583099566002,
        "persistence": 0.02394383961392316,
        "reversal_propensity": 0.8448994985643071,
        "strength": 0.03221302857118924,
        "tau": 72.006895138787,
        "uncertainty": 0.4173757402288036,
        "velocity": 0.0001696527104397393
      }
    ]
  }
}
```

## Complete D02 outputs

### Row A ReturnShape

```json
{
  "coherence": 0.9999999907876206,
  "current_level": 0.1861982523830909,
  "entity_id": "SPY",
  "forward_half_life": 15.0,
  "forward_samples": [
    {
      "level": 0.19462833422987413,
      "persistence": 0.635457786134345,
      "reversal_propensity": 0.5162175446487312,
      "strength": 0.7472646371391879,
      "tau": 1.594239365852591,
      "uncertainty": 0.30740894343298913,
      "velocity": 0.0048674281686777185
    },
    {
      "level": 0.21621895429655258,
      "persistence": 0.5292617228701793,
      "reversal_propensity": 0.5317423961307151,
      "strength": 0.6223837018319762,
      "tau": 5.551463911887316,
      "uncertainty": 0.3306962206559649,
      "velocity": 0.004053996150039425
    },
    {
      "level": 0.25056511169068635,
      "persistence": 0.40172871716234093,
      "reversal_propensity": 0.5503865050723059,
      "strength": 0.47241165441514005,
      "tau": 11.517859785277338,
      "uncertainty": 0.35866238406835116,
      "velocity": 0.0030771291449237913
    },
    {
      "level": 0.2988055001269704,
      "persistence": 0.27998008997850254,
      "reversal_propensity": 0.5681849930488588,
      "strength": 0.3292417292055194,
      "tau": 19.33132014244643,
      "uncertainty": 0.38536011603318054,
      "velocity": 0.002144568854715667
    },
    {
      "level": 0.3628285929114741,
      "persistence": 0.18003679591315763,
      "reversal_propensity": 0.5827957493169613,
      "strength": 0.21171371868485547,
      "tau": 28.88680678510959,
      "uncertainty": 0.4072762504353342,
      "velocity": 0.001379031292002958
    },
    {
      "level": 0.4450705464748999,
      "persistence": 0.10719550621243867,
      "reversal_propensity": 0.5934444510635297,
      "strength": 0.12605622718084775,
      "tau": 40.10751729615585,
      "uncertainty": 0.42324930305518693,
      "velocity": 0.0008210874709209755
    },
    {
      "level": 0.5484202090992059,
      "persistence": 0.05926219098192461,
      "reversal_propensity": 0.6004518445310421,
      "strength": 0.06968919195966662,
      "tau": 52.93342565084451,
      "uncertainty": 0.4337603932564555,
      "velocity": 0.00045393173868829594
    },
    {
      "level": 0.6761631143414789,
      "persistence": 0.030489290348908064,
      "reversal_propensity": 0.6046581681489176,
      "strength": 0.03585378759430505,
      "tau": 67.3155665570578,
      "uncertainty": 0.44006987868326874,
      "velocity": 0.0002335394009255148
    }
  ],
  "maximum_absolute_displacement": 0.489964861958388,
  "model_time": 1664525760.0,
  "path_direction": "UPWARD",
  "persistence": 0.6840391573948615,
  "projection_interval": 67.3155665570578,
  "reversal_propensity": 0.5091154115712131,
  "source_model_version": "0.2",
  "state_support_ratio": 0.6827851084628193,
  "strength": 0.8043937518637954,
  "terminal_decay_factor": 0.04457243422295505,
  "terminal_displacement": 0.489964861958388,
  "uncertainty": 0.296755743816712
}
```

### Row B ReturnShape

```json
{
  "coherence": 0.9999931783150069,
  "current_level": 0.4698558421496643,
  "entity_id": "SPY",
  "forward_half_life": 15.0,
  "forward_samples": [
    {
      "level": 0.4779056672740783,
      "persistence": 0.6166690634559729,
      "reversal_propensity": 0.7560658992139888,
      "strength": 0.8296404620303484,
      "tau": 1.7053444353880702,
      "uncertainty": 0.28412534120332605,
      "velocity": 0.004369373490073243
    },
    {
      "level": 0.49777972613807386,
      "persistence": 0.5071089788286183,
      "reversal_propensity": 0.772486014760087,
      "strength": 0.6822429604905098,
      "tau": 5.938354235363982,
      "uncertainty": 0.3087555145224734,
      "velocity": 0.0035930917569534787
    },
    {
      "level": 0.527455273135219,
      "persistence": 0.37758869942444917,
      "reversal_propensity": 0.7918976276719703,
      "strength": 0.5079918575651131,
      "tau": 12.320557698622846,
      "uncertainty": 0.3378729338902984,
      "velocity": 0.0026753832017620115
    },
    {
      "level": 0.5657921485680542,
      "persistence": 0.25661687918335097,
      "reversal_propensity": 0.8100280560386229,
      "strength": 0.3452414898475953,
      "tau": 20.678550498592156,
      "uncertainty": 0.36506857644027735,
      "velocity": 0.0018182442665848337
    },
    {
      "level": 0.6118661554346266,
      "persistence": 0.1600128563323852,
      "reversal_propensity": 0.8245064057298089,
      "strength": 0.21527452555251092,
      "tau": 30.89997415837988,
      "uncertainty": 0.38678610097705635,
      "velocity": 0.0011337619704990091
    },
    {
      "level": 0.6648314712296783,
      "persistence": 0.09189178830503945,
      "reversal_propensity": 0.8347159251176148,
      "strength": 0.12362732334736433,
      "tau": 42.90267377863407,
      "uncertainty": 0.4021003800587652,
      "velocity": 0.0006510940268760986
    },
    {
      "level": 0.7238683285913438,
      "persistence": 0.04874603453262663,
      "reversal_propensity": 0.8411823153607056,
      "strength": 0.06558085204590938,
      "tau": 56.62244002576115,
      "uncertainty": 0.41179996542340136,
      "velocity": 0.00034538724845284863
    },
    {
      "level": 0.7881583099566002,
      "persistence": 0.02394383961392316,
      "reversal_propensity": 0.8448994985643071,
      "strength": 0.03221302857118924,
      "tau": 72.006895138787,
      "uncertainty": 0.4173757402288036,
      "velocity": 0.0001696527104397393
    }
  ],
  "maximum_absolute_displacement": 0.3183024678069359,
  "model_time": 1664525820.0,
  "path_direction": "UPWARD",
  "persistence": 0.6672308993184185,
  "projection_interval": 72.006895138787,
  "reversal_propensity": 0.7484880373502629,
  "source_model_version": "0.2",
  "state_support_ratio": 0.5864884257246546,
  "strength": 0.8976642163450754,
  "terminal_decay_factor": 0.03588538785955803,
  "terminal_displacement": 0.3183024678069359,
  "uncertainty": 0.2727585484077373
}
```

D02 result: changing information received **YES**; output changed **YES** (68 of 72 flattened fields); direction represented **YES**, `path_direction`; A=`UPWARD`, B=`UPWARD`.

## Two-row propagation matrix

| Field / stage | Row A | Row B | Changed? |
|---|---:|---:|---|
| source close | 366.0 | 366.17 | YES |
| source volume | 616.0 | 2398.0 | YES |
| D01 price | 366.0 | 366.17 | YES |
| D01 state_level | 0.1861982523830909 | 0.4698558421496643 | YES |
| D01 state_velocity | 0.005239547828088794 | 0.004727626495321619 | YES |
| D01 perturbation_class | REVERSING | CONTRADICTING | YES |
| D01 uncertainty | 0.296755743816712 | 0.2727585484077373 | YES |
| D02 terminal_displacement | 0.489964861958388 | 0.3183024678069359 | YES |
| D02 maximum_absolute_displacement | 0.489964861958388 | 0.3183024678069359 | YES |
| D02 direction | UPWARD | UPWARD | NO |
| D04 Q_G / geometry_quality | NOT EXECUTED | NOT EXECUTED | NOT AVAILABLE |
| D04 Q_S / structural_quality | NOT EXECUTED | NOT EXECUTED | NOT AVAILABLE |
| D04 Q_R / risk_quality | NOT EXECUTED | NOT EXECUTED | NOT AVAILABLE |
| D04 B / base_capturability_score | NOT EXECUTED | NOT EXECUTED | NOT AVAILABLE |
| D04 G / feasibility_gate_score | NOT EXECUTED | NOT EXECUTED | NOT AVAILABLE |
| D04 H / hard_eligibility | NOT EXECUTED | NOT EXECUTED | NOT AVAILABLE |
| D04 C / capturability_score | NOT EXECUTED | NOT EXECUTED | NOT AVAILABLE |
| D04 candidate state | NOT EXECUTED | NOT EXECUTED | NOT AVAILABLE |
| D03 desired position | NOT EXECUTED | NOT EXECUTED | NOT AVAILABLE |
| D03 action_authorized | NOT EXECUTED | NOT EXECUTED | NOT AVAILABLE |
| D03 primary reason | NOT EXECUTED | NOT EXECUTED | NOT AVAILABLE |

## Information-collapse conclusion

**First information-collapse boundary: NONE OBSERVED IN THE EXECUTED REAL TRACE.**

The trace is unavailable beyond D02 because required real D04 context is absent. This is a reachability boundary, not evidence that D04 ignores changing ReturnShapes. Cause of the prior `FLAT` outputs: **NOT ESTABLISHED** under the zero-mock rules. What remains unknown is how real point-in-time D04 envelope context and real D03 position/control context would transform these two changing ReturnShapes.

## Constant fields are not automatically defects

- `D02 path_direction` remains `UPWARD` because both terminal displacements are positive: frozen mathematical behavior.
- `forward_half_life=15.0` for both: frozen model behavior at the configured lower bound.
- Entity, model/schema versions, and config hash remain constant: configuration/identity.
- D01 `data_quality=1.0` remains constant because both source rows are marked `data_valid=true`.
- D04/D03 values are unavailable, not constant.

## Stop

Diagnostic artifacts only. No repair or tuning was performed. Human review is required.
