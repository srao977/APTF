from pathlib import Path
import csv


def test_diagnostic_artifacts_exist_and_cover_all_experiments():
    root = Path(__file__).resolve().parents[1]
    diag = root / "diagnostics" / "numerical_conditioning_v0_1"

    required = [
        "D01_NUMERICAL_CONDITIONING_REPORT_V0_1.md",
        "D01_FEATURE_RANGE_REPORT_V0_1.md",
        "D01_PARAMETER_DRIFT_REPORT_V0_1.md",
        "D01_POLYNOMIAL_TERM_REPORT_V0_1.md",
        "D01_EXPERIMENT_COMPARISON_DIAGNOSTIC_V0_1.md",
        "D01_RECOMMENDED_CORRECTIONS_V0_1.md",
        "feature_statistics.csv",
        "transformed_feature_statistics.csv",
        "polynomial_term_statistics.csv",
        "interaction_term_statistics.csv",
        "target_prediction_statistics.csv",
        "parameter_statistics.csv",
        "parameter_drift_by_experiment.csv",
        "experiment_diagnostic_summary.csv",
        "first_instability_events.csv",
        "largest_contributors.csv",
        "scenario_directional_breakdown.csv",
    ]
    for name in required:
        assert (diag / name).exists(), f"Missing diagnostic artifact: {name}"

    summary_csv = diag / "experiment_diagnostic_summary.csv"
    with summary_csv.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    exp_ids = {r["experiment_id"] for r in rows}
    assert len(exp_ids) == 15
    assert "A_n1" in exp_ids and "E_n3" in exp_ids
