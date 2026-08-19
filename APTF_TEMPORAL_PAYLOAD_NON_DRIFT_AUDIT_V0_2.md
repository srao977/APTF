# APTF Temporal Payload Non-Drift Audit V0.2

Status: PASS
Date: 2026-08-18
Canonical profile: APTF-CJSON-V1

Separate frozen instances consumed the same 16 genuine setup rows. The target was then processed once through an unwrapped baseline and once through the external envelope path. No telemetry value entered a frozen payload or component call.

| Component | Field Equivalent | Baseline SHA256 | Wrapped SHA256 | Result |
|---|---|---|---|---|
| D01 | YES | `c4347b873a8bd1f8b28cef56e8c84b8be3ee0526c5746bae998d17b41d139e04` | `c4347b873a8bd1f8b28cef56e8c84b8be3ee0526c5746bae998d17b41d139e04` | PASS |
| D02 | YES | `5916efc455528390b8d23e87f5e83c4418d9cc9ec62542edf32b6d0add974808` | `5916efc455528390b8d23e87f5e83c4418d9cc9ec62542edf32b6d0add974808` | PASS |
| D04 | YES | `047191c9828b68d60e448321b8a2e61f98af56eb01249b443148526e3b2ac9b8` | `047191c9828b68d60e448321b8a2e61f98af56eb01249b443148526e3b2ac9b8` | PASS |
| D03 | YES | `e51f1613f72b4b7baf5138695c641ffab7de688228084c63096c2e7342dfccb5` | `e51f1613f72b4b7baf5138695c641ffab7de688228084c63096c2e7342dfccb5` | PASS |
| Position Controller | YES | `3f47911dab623369c8ae8ccba3c65d724370a321fefb792525401fe6f77c4e90` | `3f47911dab623369c8ae8ccba3c65d724370a321fefb792525401fe6f77c4e90` | PASS |

Post-target D01 and D04 state snapshots are field-for-field equivalent. Both canonical state hashes are `22c6168cdc6657e046fedeb5e6d57e94ac5aa981781157a36692d84b28bf81b6`.

Existing scientific identifiers remain payload-derived values. They are copied to `scientific_ids` for correlation and do not enter observation/event identity preimages except indirectly through the complete semantic payload hash. Error-path testing proves null payload/hash and an empty scientific-ID map; the original `ValueError` remains available as the local wrapper cause.

Retry testing proves equal observation, event, and payload identities with a distinct execution UUID. Injected UTC inversion changes only timing/flag telemetry and leaves SUCCESS, payload, payload hash, observation ID, and logical event ID unchanged.
