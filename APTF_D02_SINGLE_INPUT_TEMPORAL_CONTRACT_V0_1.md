# APTF D02 Single-Input Temporal Contract V0.1

Status: DIAGNOSTIC. NOT FROZEN AUTHORITY.

Entry point: `d02.v02.builder.build_return_shape(dmo, fmo)`.

## Input lineage

D02 validates equal DMO/FMO `model_time` and receives $t=1664525760.0$ in both objects. It receives DMO `trace_id` and `state_hash` as members of the input object pair, but does not copy either into its output.

## ReturnShape temporal fields

| Field | Target value | Source | Category | Wall-clock processing time? |
|---|---:|---|---|---|
| `model_time` | 1664525760.0 | direct `dmo.model_time` | E inheriting original A | NO |
| `projection_interval` | 67.3155665570578 | `fmo.interval_length` | E elapsed forward horizon | NO |
| `forward_half_life` | 15.0 | DMO | E elapsed analytical parameter | NO |
| `forward_samples[*].tau` | positive offsets ending at 67.3155665570578 | FMO samples | E elapsed offsets from model time | NO |
| `terminal_decay_factor` | derived from interval/half-life | D02 formula | E dimensionless temporal decay view | NO |

D02 output identity is canonically `(entity_id, model_time)`, here `(SPY, 1664525760.0)`. There is no separate ReturnShape ID.

## Identity transformation

Passed to output: entity, model time, source model version, analytical fields.

Dropped at output: D01 `trace_id`, D01 `state_hash`, D01 `config_hash`, source/D01 sequence, source receive-time proxy.

This is the first immutable causal-identity discontinuity. Event time remains intact, but the exact D01/source parent identity cannot be recovered from ReturnShape alone.

No `received_at`, `emitted_at`, or processing duration exists.

## Answers

- D02 knows original $t$: YES via `ReturnShape.model_time`.
- Causally tied to InputObservation(t): PARTIALLY via entity + exact event/model time and deterministic fields, not a preserved parent ID.
- D02 processing latency computable: NO.
