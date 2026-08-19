# APTF Test 003A D04 Opening-Boundary Reachability Result V0.1

Status: PASS
Date: 2026-08-18
Primary finding: **E**
Defect classification: **NONE**

## Known Evidence

Frozen open threshold is 0.75. Test 003 stored capturability values are:

`[0.22050421416872243, 0.17666062360338286, 0.25462532958949513, 0.08848558708732783, 0.28034113293008417]`.

Observed minimum is 0.08848558708732783; maximum is 0.28034113293008417; width is 0.19185554584275633; threshold gap is 0.46965886706991583. All five states were CLOSED, candidates null, D03 R31/FLAT, and controller NO_ACTION. No discrepancy was found.

Existing real evidence outside Test 003 contains C=0.4814590392445292 and 0.3605075262704571. Frozen synthetic formula vectors contain schema-valid C=1.0. These are distinguished from Test 003's real five-cycle range.

## Primary Capturability Table

| Term | Formula role | Theoretical range | Test 003 observed range | Value needed for opening | Reachable? | Limiting? | Design/implementation |
|---|---|---|---|---|---|---|---|
| H | hard zero/one eligibility | {0,1} | 1 only | 1 | reached in all cycles | no observed limitation | match |
| Q_G | endpoint efficiency | [0,1] | 0.6832134425301885–1.0 | necessary >=0.75 | algebraically/schema reachable | cycle 4 contributes attenuation | match |
| strength s | Q_S factor | [0,1] | 0.46763294686467655–0.8777636556469071 | joint `s*c*p>=0.421875` | schema reachable; D01 joint reach unknown | coupled | match |
| coherence c | Q_S factor | [0,1] | 0.0844299296192652–0.4855782805501968 | joint `s*c*p>=0.421875` | schema reachable; D01 joint reach unknown | strongly low in cycles 2/4 | match |
| persistence p | Q_S factor | [0,1] | 0.41432939878976205–0.6489344961586315 | joint `s*c*p>=0.421875` | schema reachable; D01 joint reach unknown | moderate | match |
| Q_S | structural geometric mean | [0,1] | 0.2808653989173412–0.6043625386410295 | necessary >=0.75 | algebraically reachable; end-to-end unknown | smallest family cycles 2–4 | match |
| uncertainty u | Q_R complement | [0,1] | 0.37855430696274–0.44643451950928553 | joint `(1-u)(1-r)>=0.5625` | schema reachable; D01 joint reach unknown | penalty | match |
| reversal r | Q_R complement | [0,1] | 0.5804399974703249–0.785306864585095 | joint `(1-u)(1-r)>=0.5625` | schema reachable; D01 joint reach unknown | strong penalty | match |
| Q_R | risk-quality geometric mean | [0,1] | 0.36485420599454843–0.5048353067296146 | necessary >=0.75 | algebraically reachable; end-to-end unknown | smallest family cycles 1/5 | match |
| G | minimum feasibility gate | [0,1] | 1.0 only | necessary >=0.75 | reached in all cycles | no observed limitation; can zero C generally | match |
| C | total product | [0,1] | 0.08848558708732783–0.28034113293008417 | >=0.75 | D04-local yes; end-to-end unknown | multiplicative attenuation | match |

## Exact Formula And Bounds

Frozen implementation: `CapturabilityModelV0_2.evaluate` in `d04_trading_envelope/src/aptf_d04/envelope/capturability_model.py`.

$$
C=H\,Q_G\,(scp)^{1/3}\sqrt{(1-u)(1-r)}\,\min(g_1,\ldots,g_{10}).
$$

Theoretical minimum is 0 and algebraic/schema-valid maximum is 1. The threshold 0.75 lies inside that range. A D04 schema-valid witness $Q_G=G=1$, $s=c=p=0.9$, $u=r=0.1$ yields C=0.81. Frozen vectors also establish C=1.0.

End-to-end reachable maximum through D01 state/update rules is **REACHABLE MAXIMUM NOT ESTABLISHED**. The threshold's end-to-end practical reachability is therefore UNKNOWN.

## Five-Cycle Reconstruction And Limitation

All five scores reconstruct with absolute error 0.0.

| Cycle | Q_G | Q_S | Q_R | G | C | Most limiting family | Why C<0.75 |
|---:|---:|---:|---:|---:|---:|---|---|
| 1 | 1.0 | 0.6043625386410295 | 0.36485420599454843 | 1.0 | 0.22050421416872243 | Q_R | holding others fixed would require Q_R=1.2409769832631439 |
| 2 | 1.0 | 0.3667482303751486 | 0.48169454948065005 | 1.0 | 0.17666062360338286 | Q_S | holding others fixed would require Q_S=1.5570032934950782 |
| 3 | 1.0 | 0.5043730622546775 | 0.5048353067296146 | 1.0 | 0.25462532958949513 | Q_S, near tie | moderate Q_S and Q_R multiply |
| 4 | 0.6832134425301885 | 0.2808653989173412 | 0.46112417816135437 | 1.0 | 0.08848558708732783 | Q_S plus Q_G | three attenuating factors multiply |
| 5 | 1.0 | 0.5555355673592773 | 0.5046321953114142 | 1.0 | 0.28034113293008417 | Q_R | holding others fixed would require Q_R=1.3500485730645544 |

No additive/subtractive penalty exists in D04 C. Moderate bounded factors multiply, explaining why products are smaller than individual components. H and G did not limit these cycles.

## Aperture And Hysteresis

Aperture is a separate clamped smoothed state, does not modify C, and is not compared with C for opening. Verified Test 003 values are `0.2490565349467589, 0.21285857927507087, 0.23374195443228302, 0.16111377075980543, 0.2207274518449448`.

Opening rules:

- CLOSED with C>=0.75 -> OPENING, open counter 1.
- OPENING requires consecutive C>=0.75 until counter 3 -> OPEN.
- Any C<0.75 during OPENING -> CLOSED/reset.
- OPEN with C<=0.55 -> CLOSING, close counter 1.
- CLOSING requires a second consecutive C<=0.55 -> CLOSED; C>0.55 recovers OPEN.
- Safety failure forces CLOSED immediately.

Thus one C>=0.75 is insufficient to open; three consecutive qualifying evaluations are required from CLOSED. Candidate creation occurs only after the resulting state is OPEN and no candidate exists. It has no independent numeric threshold.

## Scale, Normalization, Penalty, And Sign Audit

- Scale mismatch: **NO**. All score terms and thresholds use fractions on `[0,1]`.
- Double normalization: **NO**. Q_G is the intended one-time ratio; Q_S/Q_R are aggregation, not repeated normalization.
- Double penalization at D04 field level: **NO**. Support ratio and temporal decay were explicitly omitted to avoid reuse.
- Dependency coupling: **YES**, but not a proven defect. Coherence enters strength and then both enter Q_S; uncertainty/coherence/reversal are causally coupled upstream. This prevents independent end-to-end maximization.
- Sign/semantic inversion: **NO**. Positive quality terms increase C; uncertainty/reversal decrease C through complements; hard failure zeros C.

## Design Versus Implementation

Overall match: **YES**. Every formula term, hard gate, range, zero/invalid rule, state-machine structure, aperture ordering, and candidate condition matches frozen design. No mathematical mismatch was found.

The threshold source is `d04_trading_envelope/config/default.yaml`, consumed by `HysteresisController.next_state`. It is inherited from the earlier score, not mathematically derived and not empirically calibrated for deterministic C. **THRESHOLD RATIONALE NOT ESTABLISHED BY CURRENT AUTHORITY.** Whether it is calibrated or a placeholder is UNKNOWN.

## D04 To D03 Compression

D03 receives complete D04 evaluations, including raw C in its input/fingerprint. Once D04 state is CLOSED, R31 does not branch on raw C. Continuous differences below the opening boundary are therefore invisible to the terminal D03 target-rule path. This is a semantic property, not a defect finding.

## Primary Finding

**FINDING E: CURRENT EVIDENCE IS INSUFFICIENT TO ESTABLISH REACHABILITY.**

Precise scope: D04 algebraic/schema reachability of 0.75 is proven. End-to-end reachable maximum and practical frequency under coupled frozen D01 state rules are not established.

Defect classification: **NONE**. The missing threshold rationale/calibration and missing end-to-end reachability proof are evidence gaps, not demonstrated scale/design/implementation contradictions.

## Acceptance And Discipline

G01-G42: **42/42 PASS**.

No pipeline run, market-row read, synthetic/counterfactual execution, parameter/threshold/model change, broker/Azure action, or profitability analysis occurred. Post-audit hash verification: **91/91 PASS** (67 frozen bindings plus 24 pre-recorded Test 002/002A/003 evidence hashes).

## Next Action

Human review should distinguish: D04-local mathematical reachability (proven), end-to-end D01-driven reachability (unknown), practical prevalence (unknown), and threshold calibration rationale (not established). No threshold correction is proposed.
