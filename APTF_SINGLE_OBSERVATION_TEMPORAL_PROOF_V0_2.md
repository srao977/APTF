# APTF Single-Observation Temporal Proof V0.2

Status: PASS
Date: 2026-08-18

## Target

- Target count: 1
- Instrument: SPY
- Authoritative market event time: `2022-09-30T08:16:00Z`
- Role: `PROVIDER_EVENT`
- Normalized source row: 17
- APTF sequence number: 16, the zero-based normalized ordering ordinal
- Observation ID: `aptf:obs:v1:sha256:b6b32ddfff09ff78a63a40645ba766f04c64299701ad0f9dab172a18920d1429`
- Source stream: `aptf:source:v1:FirstRateData:SPY_1min_firstratedata:normalized_v0_1:sha256:73957227a0cc09103f7ca5ff62b011edd7c80c220017d91fb97c5fb5e6a1055d`
- Source OHLCV: 366.0 / 366.0 / 366.0 / 366.0 / 616.0
- Setup rows: 16 genuine preceding rows; no row after the target was read

## Proof Table

Table constants: `O` is the observation ID above; `S` is the source stream above; `t` is `2022-09-30T08:16:00Z`.

| Stage | Event ID | Execution ID | Observation ID | Parent Event ID | Source Stream | Sequence | Market Event Time | Received UTC | Emitted UTC | Duration ns | us | ms | Flags | Payload Type | Payload SHA256 | Status |
|---|---|---|---|---|---|---:|---|---|---|---:|---:|---:|---|---|---|---|
| E0 | `aptf:evt:v1:sha256:7352f92fc61ed3117fa7d1bd78e6bdaefd475e69d79b44afea64880fd24bd5c3` | `dd8042c7-f7b9-4d35-98f2-d68b02e08247` | O | null | S | 16 | t | `2026-08-18T16:58:25.049304Z` | `2026-08-18T16:58:25.049324Z` | 11100 | 11.1 | 0.0111 | `[]` | NormalizedObservationSourceRecord | `fcb92ce0dfdd6dca646c4c11339d60f44458f7744d5fc77571e80c013c89f15e` | SUCCESS |
| E1 | `aptf:evt:v1:sha256:06e0846ea2df24df5aa619ece64a2a770b08856ec6e74dbaa26dc8fcb27c4038` | `73eb31c0-c780-4c2e-8062-066afa350917` | O | `aptf:evt:v1:sha256:7352f92fc61ed3117fa7d1bd78e6bdaefd475e69d79b44afea64880fd24bd5c3` | S | 16 | t | `2026-08-18T16:58:25.049495Z` | `2026-08-18T16:58:25.049544Z` | 47500 | 47.5 | 0.0475 | `[]` | D01OutputPair | `c4347b873a8bd1f8b28cef56e8c84b8be3ee0526c5746bae998d17b41d139e04` | SUCCESS |
| E2 | `aptf:evt:v1:sha256:b8642eba2719eed4f243a27b359601ee7b31deda4ef4920bb5cf08c63ce7648a` | `62138767-06ba-4173-a9bd-391af1f8790d` | O | `aptf:evt:v1:sha256:06e0846ea2df24df5aa619ece64a2a770b08856ec6e74dbaa26dc8fcb27c4038` | S | 16 | t | `2026-08-18T16:58:25.049989Z` | `2026-08-18T16:58:25.050016Z` | 26200 | 26.2 | 0.0262 | `[]` | ReturnShape | `5916efc455528390b8d23e87f5e83c4418d9cc9ec62542edf32b6d0add974808` | SUCCESS |
| E3 | `aptf:evt:v1:sha256:ae029337f5b3651879151deda73481f147673b37e28e13bee55d25d9331f2ef2` | `5bdf5f7b-8486-45bb-b1c0-8a52515910c4` | O | `aptf:evt:v1:sha256:b8642eba2719eed4f243a27b359601ee7b31deda4ef4920bb5cf08c63ce7648a` | S | 16 | t | `2026-08-18T16:58:25.050342Z` | `2026-08-18T16:58:25.050372Z` | 28900 | 28.9 | 0.0289 | `[]` | EnvelopeEvaluation | `047191c9828b68d60e448321b8a2e61f98af56eb01249b443148526e3b2ac9b8` | SUCCESS |
| E4 | `aptf:evt:v1:sha256:ced0013a8f795a664346a94ea140ff0d1462cf2474c1ed8d32d5a7977a8837e5` | `0aadbd90-900e-4f19-a4a9-2231a2eb3b88` | O | `aptf:evt:v1:sha256:ae029337f5b3651879151deda73481f147673b37e28e13bee55d25d9331f2ef2` | S | 16 | t | `2026-08-18T16:58:25.050543Z` | `2026-08-18T16:58:25.050620Z` | 75400 | 75.4 | 0.0754 | `[]` | DecisionRecord | `e51f1613f72b4b7baf5138695c641ffab7de688228084c63096c2e7342dfccb5` | SUCCESS |
| E5 | `aptf:evt:v1:sha256:6a75948b7568f3693e4f4f58319bb6d83c0faea2e56a5e52b70ec81785ad32e8` | `feab9bc8-47b0-4e36-99ac-ff2d6f2e2c04` | O | `aptf:evt:v1:sha256:ced0013a8f795a664346a94ea140ff0d1462cf2474c1ed8d32d5a7977a8837e5` | S | 16 | t | `2026-08-18T16:58:25.050734Z` | `2026-08-18T16:58:25.050750Z` | 14500 | 14.5 | 0.0145 | `[]` | PositionTransitionPlan | `3f47911dab623369c8ae8ccba3c65d724370a321fefb792525401fe6f77c4e90` | SUCCESS |

Every row also carries the same observation ID, source stream, sequence 16, and market event time. Every event ID is distinct. Every execution ID is a unique UUIDv4. The single clock-domain ID is unchanged E0-E5, and each duration equals its local monotonic emit minus receive sample.

## Identity And Temporal Results

P01-P10: PASS. One observation identity is inherited; six logical identities are distinct; six execution attempts are unique; E0-E5 parent continuity is complete; existing scientific identifiers are copied without redefinition.

T01-T10: PASS. Source event time is immutable; all UTC and monotonic samples are present; all durations are nonnegative same-domain differences; model/control times are not used as telemetry; inversion behavior passes an injected-clock test.

Terminal semantic output is a complete `PositionTransitionPlan`, not a detached verb. Its ordered execution verbs are `["NO_ACTION"]` for explicit actual state FLAT, no pending target, and enabled/available control context.
