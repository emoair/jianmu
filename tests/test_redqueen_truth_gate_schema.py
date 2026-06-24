from jianmu.self_learning.darwinforge.redqueen_truth_gate_schema import RedQueenTruthGateConfig, STILL_NOT_PROVEN_MIRROR


def test_redqueen_truth_gate_schema_defaults() -> None:
    cfg = RedQueenTruthGateConfig()
    assert cfg.reject_old_v1_0_8_6_8h_claim is True
    assert "true 8h RedQueen stability rerun after time repair" in STILL_NOT_PROVEN_MIRROR

