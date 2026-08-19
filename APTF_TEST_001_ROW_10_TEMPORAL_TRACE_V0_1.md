# APTF Test 001 Row 10 Temporal Trace V0.1

Status: PASS / TEST EVIDENCE ONLY

All rows below belong to physical CSV row 10, data index/sequence 8, market time `2022-09-30T08:08:00Z`, role `PROVIDER_EVENT`, and observation ID `aptf:obs:v1:sha256:b509f4eab70253e21966fc6747eeec80329585c71e96a22b58cfa7f7dc21e696`.

| Stage | Market event time UTC | Event ID | Execution ID | Parent Event ID | Received UTC | Emitted UTC | Duration ns |
|---|---|---|---|---|---|---|---:|
| E0 Source | 2022-09-30T08:08:00Z | `aptf:evt:v1:sha256:a4927b853c27014cedf619fe813809a4422be6e196ceec10b58f27d47fed5143` | `74e420ca-5f92-46ad-9557-6f9a513d4426` | null | 2026-08-18T17:17:08.449801Z | 2026-08-18T17:17:08.449821Z | 12500 |
| E1 D01 | 2022-09-30T08:08:00Z | `aptf:evt:v1:sha256:1bed3437d89a99bf77b9ef10297b7ed3fbaf86ee486dcf860c9fcf10819263ae` | `7c5e06e7-315f-4906-8c42-456ff7e6927c` | E0 event ID | 2026-08-18T17:17:08.450009Z | 2026-08-18T17:17:08.450056Z | 45800 |
| E2 D02 | 2022-09-30T08:08:00Z | `aptf:evt:v1:sha256:44aa341620badc4c175702c5e323e28bcca2ec5f3841d7e3e0258888da72c13a` | `74b6943a-7ff4-4982-8c47-bfdf91ef8b5d` | E1 event ID | 2026-08-18T17:17:08.450499Z | 2026-08-18T17:17:08.450532Z | 32000 |
| E3 D04 | 2022-09-30T08:08:00Z | `aptf:evt:v1:sha256:71218ec92bd3a2797a1ff6fc212a34642f6825a6c0c5c08ea7cc7e96c68f23c2` | `81cd4064-9d48-46b9-aa28-a75fb1f562c2` | E2 event ID | 2026-08-18T17:17:08.450869Z | 2026-08-18T17:17:08.450897Z | 26700 |
| E4 D03 | 2022-09-30T08:08:00Z | `aptf:evt:v1:sha256:7e08cd9ab07bbd9d5cc4f1060bbd0374dd8d99d4ed1b550c63f3826d10f405ce` | `cb0425e6-dab6-4eb7-a364-6ca4d2ee160c` | E3 event ID | 2026-08-18T17:17:08.451071Z | 2026-08-18T17:17:08.451127Z | 55000 |
| E5 Controller | 2022-09-30T08:08:00Z | `aptf:evt:v1:sha256:f4e75c7d667d91fc6fd0aefb055a681f6119ef6c4770237316d9f51711edfc8b` | `bc6d2781-7045-4e48-90e3-71244ff95af5` | E4 event ID | 2026-08-18T17:17:08.451249Z | 2026-08-18T17:17:08.451258Z | 8200 |

All stages used runtime instance `57699654-27a7-401c-8f11-c638de22436d` and clock domain `90f85c1c-8d51-4930-bfc1-25b82f2b679d`. Every duration equals the corresponding same-domain monotonic emit minus receive sample, is nonnegative, and carries no wall-clock inversion flag.

## Verdict

- Market time preserved E0-E5: PASS
- Observation identity preserved E0-E5: PASS
- Immediate parent lineage complete: PASS
- Six unique logical events: PASS
- Six unique execution UUIDv4 values: PASS
- Aware UTC receive/emit present: PASS
- Integer nanosecond durations valid: PASS

Processing speed is telemetry only and is not evidence of mathematical correctness.
