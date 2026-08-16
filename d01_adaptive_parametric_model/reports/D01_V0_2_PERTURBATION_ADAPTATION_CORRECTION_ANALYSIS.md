# D01 v0.2 Perturbation Adaptation Correction Analysis

## Scope
- Stage A static inspection only.
- No source correction was applied before this report.
- Authority: D01_ADAPTIVE_PARAMETRIC_MODEL_V0_2_IMPLEMENTATION_DESIGN.md.

## Authoritative Evidence Reviewed
- output/d01_v02_perturbation_adaptation_forensics/D01_V0_2_PERTURBATION_ADAPTATION_FORENSIC_AUDIT.md
- output/d01_v02_perturbation_adaptation_forensics/perturbation_adaptation_parameter_trace.csv
- output/d01_v02_perturbation_adaptation_forensics/perturbation_adaptation_on_off_deltas.csv
- output/d01_v02_perturbation_adaptation_forensics/on_off_pairing_verification.json

## Design Requirement
- Section 11 defines adaptive update and learning-rate factorization:
	- eta_k(t) = eta_0,k * f_S(S_t) * f_U(U_t) * f_Q(Q_t)
- Section 13 states perturbations may change adaptive learning rates.
- Ablation ON/OFF must enable/disable perturbation contribution (neutral OFF behavior).

## Static Path Inspection

### A) Config field controlling perturbation-responsive adaptation
- File: src/d01/v02/config.py
- Class: AblationConfig
- Field: perturbation_adaptation: bool = True
- ON behavior: model may use perturbation multiplier.
- OFF behavior: perturbation multiplier is forced neutral in model step.

### B) Perturbation magnitude/classification computation
- File: src/d01/v02/perturbation.py
- Function: classify_perturbation
- Current magnitude proxy:
	- q = clip(innovation / (1 + innovation), 0, 1)
- Current class logic:
	- STRUCTURAL if source_quality < 0.5
	- REVERSING if sign_flip and q >= reversing threshold
	- CONTRADICTING if abs(velocity - prev_velocity) >= contradicting threshold
	- REINFORCING if q >= reinforcing threshold
	- else NONE

### C) Perturbation adaptation multiplier computation
- File: src/d01/v02/perturbation.py
- Function: classify_perturbation
- Current multiplier behavior by class:
	- NONE -> 1.0
	- STRUCTURAL/UNKNOWN -> 1.0
	- REINFORCING -> 1.1 (hardcoded)
	- CONTRADICTING -> 1.2 (hardcoded)
	- REVERSING -> cfg.adaptation_multiplier_bounds[1]

### D) Effective learning-rate computation
- File: src/d01/v02/model.py and src/d01/v02/adaptation.py
- Model branch:
	- adaptive_mult = perturbation_multiplier if perturbation_adaptation else 1.0
- Learning rate application:
	- eta = eta0 * max(0.2, 1-uncertainty) * max(0.5, strength) * perturbation_multiplier

### E) Adaptive parameter update computation
- File: src/d01/v02/adaptation.py
- Function: update_parameters
- Update driver:
	- gradient = (strength - uncertainty) * 0.1
- Raw update and projection are computed from eta and gradient.

### F) ON/OFF branch behavior
- File: src/d01/v02/model.py
- ON branch: uses classify_perturbation multiplier as adaptive_mult.
- OFF branch: forces adaptive_mult = 1.0.
- Forensic pairing confirms only this ablation flag differs across paired runs.

## Why ON and OFF Become Identical
1. For S05 and S06 forensic trajectories, classify_perturbation returns class NONE throughout event windows.
2. NONE returns perturbation multiplier 1.0.
3. OFF path also forces 1.0.
4. Therefore ON and OFF both use identical perturbation multiplier, identical eta, identical raw/projection updates, and identical final parameter state.

## Evidence for the Neutralization Stage
- Forensic audit classification: PERTURBATION_MULTIPLIER_ALWAYS_NEUTRAL.
- divergence_stages.csv: first divergence stage CONFIG, first equal stage PERTURBATION_MULTIPLIER (S05/S06).
- perturbation_adaptation_on_off_deltas.csv: all perturbation multiplier and eta deltas are 0 for paired observations.
- perturbation_adaptation_trace.csv: event rows show perturbation_class = NONE and effective_perturbation_multiplier = 1.0.

## Exact Root Cause
- The ablation switch is wired and reaches the model correctly.
- The perturbation classifier/magnitude path for these scenarios does not produce non-NONE classes.
- Because NONE maps to neutral multiplier 1.0, the ON branch collapses to OFF behavior.
- This is a perturbation adaptation implementation defect relative to design intent that perturbations may change adaptive learning rates via f_Q.

## Existing Logic Reuse Check
- No alternate perturbation-to-adaptation mapping exists elsewhere in src/d01/v02.
- Current class-to-multiplier logic partially hardcodes values and does not provide a robust bounded response for meaningful perturbation states in these trajectories.

## Correction Classification
- IMPLEMENTING_MISSING_DESIGN_LOGIC

## Authorization Gate Decision
- A) Conflict with design: YES.
- B) Minimal correction without redesign: YES.
- Result: CORRECTION AUTHORIZED.
