# APTF Test 004A Backward Boundary Plan V0.1

Status: EXECUTED MATHEMATICAL EVIDENCE ANALYSIS
Date: 2026-08-18

## Scope

Use only stored Test 004 cycles for physical rows 10-14 and corrected D04 V0.2.2 equation authority. Perform JSON/arithmetic analysis only. Do not import or call D01/D02/D04/D03/controller, read CSV data, process row 15, scan additional rows, construct synthetic market values, or modify code/configuration/tests.

## Evidence

Twelve Test 004 artifacts and nineteen corrected D04 authority/implementation bindings passed pre-audit verification. Stored Test 004 establishes five corrected cycles, row 15 unread, H=1, G=1, and exact formula terms.

## Method

For each cycle solve `H*Q_G*Q_S*Q_R*G=0.75` one factor at a time; expand Q_S into strength/coherence/persistence; expand Q_R into uncertainty/reversal; expand Q_G into `|D|/M`; calculate one-factor and two-factor unit-bound ceilings; record exact joint boundary; map upstream coupling; and distinguish declared bounds from proven reachable states.

All calculations retain Python binary64 values serialized without manual rounding. Human tables may display fewer digits but JSON is authoritative.

## Classification Discipline

- Level 1: declared unit-bound feasibility.
- Level 2: conditional feasibility holding other Test 004 values fixed.
- Level 3: actual joint reachability under frozen coupled D01/D02 equations.

Level 3 is not inferred from Levels 1-2. No replacement threshold is calculated or proposed.
