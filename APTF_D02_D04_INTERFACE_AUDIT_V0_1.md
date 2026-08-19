# APTF D02-D04 Interface Audit V0.1

Diagnostic only. No implementation authority.

## Boundary contract

- Producer type: `d02.v02.models.ReturnShape`
- Consumer call: `TradingEnvelope.process(return_shape: ReturnShape, context: EnvelopeContext)`
- ReturnShape mapping: direct object, no adapter.
- Additional required input: `aptf_d04.models.envelope_context.EnvelopeContext` with 13 required fields.

## Complete real D02 payloads available at the boundary

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

## D04 input separation

### A. D02-originating fields

All 17 top-level ReturnShape fields and all 56 nested ForwardSample leaves cross directly. They differ in 68 of 72 flattened fields.

### B. Elsewhere-originating EnvelopeContext fields

| Field | Real provenance available? | Existing replay value | Classification |
|---|---|---:|---|
| evaluation_time | YES: D01 observation event_time | A=1664525760.0, B=1664525820.0 | REQUIRED ADAPTER VALUE |
| data_integrity | YES: derived from source data_valid | 1.0 | REQUIRED ADAPTER VALUE |
| market_eligible | NO | true | MOCK/SYNTHETIC VALUE |
| clock_event_quality | NO | 1.0 | MOCK/SYNTHETIC VALUE |
| capital_available | NO | 1.0 | MOCK/SYNTHETIC VALUE |
| portfolio_capacity | NO | 1.0 | MOCK/SYNTHETIC VALUE |
| position_capacity | NO | 1.0 | MOCK/SYNTHETIC VALUE |
| liquidity_quality | NO | 1.0 | MOCK/SYNTHETIC VALUE |
| spread_quality | NO | 1.0 | MOCK/SYNTHETIC VALUE |
| latency_quality | NO | 1.0 | MOCK/SYNTHETIC VALUE |
| execution_feasibility | NO | 1.0 | MOCK/SYNTHETIC VALUE |
| risk_capacity | NO | 1.0 | MOCK/SYNTHETIC VALUE |
| broker_health | NO | 1.0 | MOCK/SYNTHETIC VALUE |

## Required stop

D04 was **not invoked**. Consequently Q_G=`geometry_quality`, Q_S=`structural_quality`, Q_R=`risk_quality`, B=`base_capturability_score`, G=`feasibility_gate_score`, H=`hard_eligibility`, C=`capturability_score`, aperture, hysteresis, candidate state, and candidate `path_direction` are all **NOT AVAILABLE** for both target events.

The code proves D04 would receive changing ReturnShapes, but this audit cannot truthfully answer whether D04 internal state changes because the required real context does not exist in the source.

## Configuration discrepancy

The replay sets `CapturabilityModelV0_2.critical_data_integrity_threshold=0.0` and `SafetyConfig.critical_data_integrity_threshold=0.0`; `d04_trading_envelope/config/default.yaml` specifies `0.2`. The replay comment says the override allows minimal integrity "for proof." Classification: **UNAUTHORIZED DEFAULT / REPLAY CONFIGURATION DEVIATION**. No repair was made.
