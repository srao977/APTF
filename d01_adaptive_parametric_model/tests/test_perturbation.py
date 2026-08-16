from aptf_d01.signals.perturbation_detector import PerturbationDetector, PerturbationThresholds


def test_perturbation_detects_threshold_cross() -> None:
    d = PerturbationDetector(
        PerturbationThresholds(0.002, 0.001, 0.001, 1.5, 1000.0, 0.05)
    )
    p = d.detect("TEST_ENTITY", 1.0, 0.003, 0.0015, 0.0012, 2.0, 1500.0, 0.06)
    assert p.magnitude > 0.0
    assert len(p.reason_codes) >= 1
