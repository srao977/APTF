# D04 Trading Envelope Implementation Trace v0.2

## Status

IMPLEMENTED AND EXECUTABLY VERIFIED on the existing `d04_trading_envelope` package. No parallel D04 implementation was created.

## Authority

- D01 architecture freeze: `B6ED942E41EC1C72350CF9247597E5819A942DBE9D04770C23E243204165B235`
- D02 design freeze: `6FC2D51FDA74284B7866B67DE2B6EA7025F9F3599606E2A9945FCF53D07A7CE6`
- D02 implementation freeze: `C8029C4B9608547BBF7960F05E4F8613480C4FB2BF8594D94482516B954F7E72`
- D04 modernization design freeze: `B5C489D060629A91DDED5B2C6EAA4076F6273AF05AED3480659CE649A1050E51`

All four hashes were re-verified immediately before implementation closeout.

## Execution path

1. The input boundary consumes `d02.v02.models.ReturnShape` directly; the local module only re-exports the frozen type.
2. `CapturabilityModelV0_2` validates deterministic-view invariants, then computes exact `Q_G`, `Q_S`, `Q_R`, `B`, ten-field minimum `G`, hard eligibility `H`, and `C=H*B*G`.
3. `TradingEnvelope.process` enforces per-entity model-time ordering, supersession, context reevaluation, projection validity, and immediate safety closure.
4. Normal flow preserves hysteresis before aperture. Safety flow bypasses persistence, sets aperture exactly to zero, resets hysteresis, and invalidates a candidate.
5. Candidate identity is deterministic RFC 3986 percent encoding plus binary64 `.17g` time formatting.
6. The runtime emits only factual events and serializes the canonical ReturnShape, 13-field context, and 23-field evaluation.

## Preserved assets

The existing aperture model, hysteresis controller, four-state ontology, lifecycle transition mapping, event bus, audit logger architecture, scenario loader, CLI entry point, and realtime loop remain in place. Their interfaces were adapted only where the frozen contract required it.

## Controlled replacements

The retired 16-field shadow ReturnShape, weighted legacy capturability components, local position/continuation semantics, legacy opportunity payload, untyped context metadata, and old score-based scenario fixtures were removed. Synthetic scenarios now state natural geometry/state and causal context and construct the actual D02 type.

## Governance

No historical replay, final backtest, reserve access, outcome-label inspection, learning, fitting, random identity, or semantic wall clock was used. The pre-existing deletion of `d04_trading_envelope/output/run_all_v02.txt` was not made, restored, hashed, or included in this implementation.
