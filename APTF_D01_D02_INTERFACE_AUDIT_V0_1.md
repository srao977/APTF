# APTF D01-D02 Interface Audit V0.1

Diagnostic only. No implementation authority.

## Boundary

- Producer: `D01V02Model.step(NormalizedObservation) -> tuple[DMOOutput, FMOOutput]`
- Consumer: `build_return_shape(dmo: DMOOutput, fmo: FMOOutput) -> ReturnShape`
- Relationship: **DIRECT PAIR**
- Same objects/types: **YES**; the exact D01 objects are passed to D02.
- Adapter: **NONE**
- Window: **NONE**
- D02 accumulated state: **NONE**
- Harness-synthesized D02 fields: **0**

## Field provenance

| D02 input field | Row A | Row B | Changed? | Provenance | Defaulted? | Synthesized by harness? |
|---|---:|---:|---|---|---|---|
| `dmo.model_time` | `1664525760.0` | `1664525820.0` | YES | D01 `DMOOutput.model_time` | NO | NO |
| `dmo.entity_id` | `"SPY"` | `"SPY"` | NO | D01 `DMOOutput.entity_id` | NO | NO |
| `dmo.model_version` | `"0.2"` | `"0.2"` | NO | D01 `DMOOutput.model_version` | NO | NO |
| `dmo.state_level` | `0.1861982523830909` | `0.4698558421496643` | YES | D01 `DMOOutput.state_level` | NO | NO |
| `dmo.state_velocity` | `0.005239547828088794` | `0.004727626495321619` | YES | D01 `DMOOutput.state_velocity` | NO | NO |
| `dmo.state_acceleration` | `6.0582676702565786e-05` | `-8.532022211364249e-06` | YES | D01 `DMOOutput.state_acceleration` | NO | NO |
| `dmo.state_curvature` | `6.0580182036429116e-05` | `-8.531736177522575e-06` | YES | D01 `DMOOutput.state_curvature` | NO | NO |
| `dmo.strength` | `0.8043937518637954` | `0.8976642163450754` | YES | D01 `DMOOutput.strength` | NO | NO |
| `dmo.coherence` | `0.9999999907876206` | `0.9999931783150069` | YES | D01 `DMOOutput.coherence` | NO | NO |
| `dmo.persistence` | `0.6840391573948615` | `0.6672308993184185` | YES | D01 `DMOOutput.persistence` | NO | NO |
| `dmo.perturbation_magnitude` | `0.027385217798428497` | `0.003949663883064501` | YES | D01 `DMOOutput.perturbation_magnitude` | NO | NO |
| `dmo.perturbation_class` | `"REVERSING"` | `"CONTRADICTING"` | YES | D01 `DMOOutput.perturbation_class` | NO | NO |
| `dmo.uncertainty` | `0.296755743816712` | `0.2727585484077373` | YES | D01 `DMOOutput.uncertainty` | NO | NO |
| `dmo.reversal_propensity` | `0.5091154115712131` | `0.7484880373502629` | YES | D01 `DMOOutput.reversal_propensity` | NO | NO |
| `dmo.state_support_ratio` | `0.6827851084628193` | `0.5864884257246546` | YES | D01 `DMOOutput.state_support_ratio` | NO | NO |
| `dmo.observation_half_life` | `15.0` | `15.0` | NO | D01 `DMOOutput.observation_half_life` | NO | NO |
| `dmo.forward_half_life` | `15.0` | `15.0` | NO | D01 `DMOOutput.forward_half_life` | NO | NO |
| `dmo.parameter_state` | `{"ref_alpha": 0.051562086467087535}` | `{"ref_alpha": 0.05176646431379669}` | YES | D01 `DMOOutput.parameter_state` | NO | NO |
| `dmo.parameter_update_magnitude` | `{"ref_alpha": 0.00014554768354110847}` | `{"ref_alpha": 0.00020437784670915282}` | YES | D01 `DMOOutput.parameter_update_magnitude` | NO | NO |
| `dmo.data_quality` | `1.0` | `1.0` | NO | D01 `DMOOutput.data_quality` | NO | NO |
| `dmo.model_health` | `"DEGRADED_DATA"` | `"DEGRADED_DATA"` | NO | D01 `DMOOutput.model_health` | NO | NO |
| `dmo.dmo_schema_version` | `"0.2.0"` | `"0.2.0"` | NO | D01 `DMOOutput.dmo_schema_version` | NO | NO |
| `dmo.fmo_schema_version` | `"0.2.0"` | `"0.2.0"` | NO | D01 `DMOOutput.fmo_schema_version` | NO | NO |
| `dmo.config_hash` | `"30DE0D125752D222FED57D80581C73939C4C0BA9ABD5F6FDAA9CFCB9970BF8DD"` | `"30DE0D125752D222FED57D80581C73939C4C0BA9ABD5F6FDAA9CFCB9970BF8DD"` | NO | D01 `DMOOutput.config_hash` | NO | NO |
| `dmo.state_hash` | `"FCCB692875A5CF82F914D2E27640C3A503998D00968F9A711E439589AD9BEC03"` | `"0237A5C4ABA304EB7C9D5B1BFC651A080250A381B0E655D402EFBC6790B95509"` | YES | D01 `DMOOutput.state_hash` | NO | NO |
| `dmo.trace_id` | `"SPY:17"` | `"SPY:18"` | YES | D01 `DMOOutput.trace_id` | NO | NO |
| `fmo.model_time` | `1664525760.0` | `1664525820.0` | YES | D01 `FMOOutput.model_time` | NO | NO |
| `fmo.entity_id` | `"SPY"` | `"SPY"` | NO | D01 `FMOOutput.entity_id` | NO | NO |
| `fmo.interval_length` | `67.3155665570578` | `72.006895138787` | YES | D01 `FMOOutput.interval_length` | NO | NO |
| `fmo.samples[*].{tau,level,velocity,uncertainty,strength,persistence,reversal_propensity}` | See complete payload/diff below | See complete payload/diff below | YES (all sample leaves changed) | D01 `FMOOutput.samples` | NO | NO |

## Complete payloads

### Row A
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

### Row B
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

## Complete field-level diff

| Field | Row A | Row B | Classification |
|---|---:|---:|---|
| `dmo.coherence` | `0.9999999907876206` | `0.9999931783150069` | CHANGED |
| `dmo.config_hash` | `"30DE0D125752D222FED57D80581C73939C4C0BA9ABD5F6FDAA9CFCB9970BF8DD"` | `"30DE0D125752D222FED57D80581C73939C4C0BA9ABD5F6FDAA9CFCB9970BF8DD"` | SAME |
| `dmo.data_quality` | `1.0` | `1.0` | SAME |
| `dmo.dmo_schema_version` | `"0.2.0"` | `"0.2.0"` | SAME |
| `dmo.entity_id` | `"SPY"` | `"SPY"` | SAME |
| `dmo.fmo_schema_version` | `"0.2.0"` | `"0.2.0"` | SAME |
| `dmo.forward_half_life` | `15.0` | `15.0` | SAME |
| `dmo.model_health` | `"DEGRADED_DATA"` | `"DEGRADED_DATA"` | SAME |
| `dmo.model_time` | `1664525760.0` | `1664525820.0` | CHANGED |
| `dmo.model_version` | `"0.2"` | `"0.2"` | SAME |
| `dmo.observation_half_life` | `15.0` | `15.0` | SAME |
| `dmo.parameter_state.ref_alpha` | `0.051562086467087535` | `0.05176646431379669` | CHANGED |
| `dmo.parameter_update_magnitude.ref_alpha` | `0.00014554768354110847` | `0.00020437784670915282` | CHANGED |
| `dmo.persistence` | `0.6840391573948615` | `0.6672308993184185` | CHANGED |
| `dmo.perturbation_class` | `"REVERSING"` | `"CONTRADICTING"` | CHANGED |
| `dmo.perturbation_magnitude` | `0.027385217798428497` | `0.003949663883064501` | CHANGED |
| `dmo.reversal_propensity` | `0.5091154115712131` | `0.7484880373502629` | CHANGED |
| `dmo.state_acceleration` | `6.0582676702565786e-05` | `-8.532022211364249e-06` | CHANGED |
| `dmo.state_curvature` | `6.0580182036429116e-05` | `-8.531736177522575e-06` | CHANGED |
| `dmo.state_hash` | `"FCCB692875A5CF82F914D2E27640C3A503998D00968F9A711E439589AD9BEC03"` | `"0237A5C4ABA304EB7C9D5B1BFC651A080250A381B0E655D402EFBC6790B95509"` | CHANGED |
| `dmo.state_level` | `0.1861982523830909` | `0.4698558421496643` | CHANGED |
| `dmo.state_support_ratio` | `0.6827851084628193` | `0.5864884257246546` | CHANGED |
| `dmo.state_velocity` | `0.005239547828088794` | `0.004727626495321619` | CHANGED |
| `dmo.strength` | `0.8043937518637954` | `0.8976642163450754` | CHANGED |
| `dmo.trace_id` | `"SPY:17"` | `"SPY:18"` | CHANGED |
| `dmo.uncertainty` | `0.296755743816712` | `0.2727585484077373` | CHANGED |
| `fmo.entity_id` | `"SPY"` | `"SPY"` | SAME |
| `fmo.interval_length` | `67.3155665570578` | `72.006895138787` | CHANGED |
| `fmo.model_time` | `1664525760.0` | `1664525820.0` | CHANGED |
| `fmo.samples[0].level` | `0.19462833422987413` | `0.4779056672740783` | CHANGED |
| `fmo.samples[0].persistence` | `0.635457786134345` | `0.6166690634559729` | CHANGED |
| `fmo.samples[0].reversal_propensity` | `0.5162175446487312` | `0.7560658992139888` | CHANGED |
| `fmo.samples[0].strength` | `0.7472646371391879` | `0.8296404620303484` | CHANGED |
| `fmo.samples[0].tau` | `1.594239365852591` | `1.7053444353880702` | CHANGED |
| `fmo.samples[0].uncertainty` | `0.30740894343298913` | `0.28412534120332605` | CHANGED |
| `fmo.samples[0].velocity` | `0.0048674281686777185` | `0.004369373490073243` | CHANGED |
| `fmo.samples[1].level` | `0.21621895429655258` | `0.49777972613807386` | CHANGED |
| `fmo.samples[1].persistence` | `0.5292617228701793` | `0.5071089788286183` | CHANGED |
| `fmo.samples[1].reversal_propensity` | `0.5317423961307151` | `0.772486014760087` | CHANGED |
| `fmo.samples[1].strength` | `0.6223837018319762` | `0.6822429604905098` | CHANGED |
| `fmo.samples[1].tau` | `5.551463911887316` | `5.938354235363982` | CHANGED |
| `fmo.samples[1].uncertainty` | `0.3306962206559649` | `0.3087555145224734` | CHANGED |
| `fmo.samples[1].velocity` | `0.004053996150039425` | `0.0035930917569534787` | CHANGED |
| `fmo.samples[2].level` | `0.25056511169068635` | `0.527455273135219` | CHANGED |
| `fmo.samples[2].persistence` | `0.40172871716234093` | `0.37758869942444917` | CHANGED |
| `fmo.samples[2].reversal_propensity` | `0.5503865050723059` | `0.7918976276719703` | CHANGED |
| `fmo.samples[2].strength` | `0.47241165441514005` | `0.5079918575651131` | CHANGED |
| `fmo.samples[2].tau` | `11.517859785277338` | `12.320557698622846` | CHANGED |
| `fmo.samples[2].uncertainty` | `0.35866238406835116` | `0.3378729338902984` | CHANGED |
| `fmo.samples[2].velocity` | `0.0030771291449237913` | `0.0026753832017620115` | CHANGED |
| `fmo.samples[3].level` | `0.2988055001269704` | `0.5657921485680542` | CHANGED |
| `fmo.samples[3].persistence` | `0.27998008997850254` | `0.25661687918335097` | CHANGED |
| `fmo.samples[3].reversal_propensity` | `0.5681849930488588` | `0.8100280560386229` | CHANGED |
| `fmo.samples[3].strength` | `0.3292417292055194` | `0.3452414898475953` | CHANGED |
| `fmo.samples[3].tau` | `19.33132014244643` | `20.678550498592156` | CHANGED |
| `fmo.samples[3].uncertainty` | `0.38536011603318054` | `0.36506857644027735` | CHANGED |
| `fmo.samples[3].velocity` | `0.002144568854715667` | `0.0018182442665848337` | CHANGED |
| `fmo.samples[4].level` | `0.3628285929114741` | `0.6118661554346266` | CHANGED |
| `fmo.samples[4].persistence` | `0.18003679591315763` | `0.1600128563323852` | CHANGED |
| `fmo.samples[4].reversal_propensity` | `0.5827957493169613` | `0.8245064057298089` | CHANGED |
| `fmo.samples[4].strength` | `0.21171371868485547` | `0.21527452555251092` | CHANGED |
| `fmo.samples[4].tau` | `28.88680678510959` | `30.89997415837988` | CHANGED |
| `fmo.samples[4].uncertainty` | `0.4072762504353342` | `0.38678610097705635` | CHANGED |
| `fmo.samples[4].velocity` | `0.001379031292002958` | `0.0011337619704990091` | CHANGED |
| `fmo.samples[5].level` | `0.4450705464748999` | `0.6648314712296783` | CHANGED |
| `fmo.samples[5].persistence` | `0.10719550621243867` | `0.09189178830503945` | CHANGED |
| `fmo.samples[5].reversal_propensity` | `0.5934444510635297` | `0.8347159251176148` | CHANGED |
| `fmo.samples[5].strength` | `0.12605622718084775` | `0.12362732334736433` | CHANGED |
| `fmo.samples[5].tau` | `40.10751729615585` | `42.90267377863407` | CHANGED |
| `fmo.samples[5].uncertainty` | `0.42324930305518693` | `0.4021003800587652` | CHANGED |
| `fmo.samples[5].velocity` | `0.0008210874709209755` | `0.0006510940268760986` | CHANGED |
| `fmo.samples[6].level` | `0.5484202090992059` | `0.7238683285913438` | CHANGED |
| `fmo.samples[6].persistence` | `0.05926219098192461` | `0.04874603453262663` | CHANGED |
| `fmo.samples[6].reversal_propensity` | `0.6004518445310421` | `0.8411823153607056` | CHANGED |
| `fmo.samples[6].strength` | `0.06968919195966662` | `0.06558085204590938` | CHANGED |
| `fmo.samples[6].tau` | `52.93342565084451` | `56.62244002576115` | CHANGED |
| `fmo.samples[6].uncertainty` | `0.4337603932564555` | `0.41179996542340136` | CHANGED |
| `fmo.samples[6].velocity` | `0.00045393173868829594` | `0.00034538724845284863` | CHANGED |
| `fmo.samples[7].level` | `0.6761631143414789` | `0.7881583099566002` | CHANGED |
| `fmo.samples[7].persistence` | `0.030489290348908064` | `0.02394383961392316` | CHANGED |
| `fmo.samples[7].reversal_propensity` | `0.6046581681489176` | `0.8448994985643071` | CHANGED |
| `fmo.samples[7].strength` | `0.03585378759430505` | `0.03221302857118924` | CHANGED |
| `fmo.samples[7].tau` | `67.3155665570578` | `72.006895138787` | CHANGED |
| `fmo.samples[7].uncertainty` | `0.44006987868326874` | `0.4173757402288036` | CHANGED |
| `fmo.samples[7].velocity` | `0.0002335394009255148` | `0.0001696527104397393` | CHANGED |

## ReturnShape semantics from frozen code

- Magnitude: `terminal_displacement`, `maximum_absolute_displacement`.
- Shape: `projection_interval`, `forward_half_life`, `forward_samples`, `terminal_decay_factor`.
- Direction: `path_direction`, computed solely from the sign of terminal displacement.
- Uncertainty/confidence-related: top-level `uncertainty`, `strength`, `coherence`, `persistence`, `reversal_propensity`, `state_support_ratio`, plus per-sample uncertainty/strength/persistence/reversal.

Answers: D02 receives changing information **YES**. D02 output changes **YES**. Direction represented **YES**: A=`UPWARD`, B=`UPWARD`.
