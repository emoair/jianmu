from jianmu.self_learning.darwinforge.opt_true8h_readiness import build_opt_true8h_readiness


def test_opt_display_gate_requires_live_progress(tmp_path) -> None:
    readiness = build_opt_true8h_readiness(tmp_path, {"opt_display_smoke_gate_passed": False})
    assert readiness["recommended_claim_level"] == "opt_display_gate_failed"


def test_opt_display_gate_blocks_8h_when_no_progress(tmp_path) -> None:
    readiness = build_opt_true8h_readiness(tmp_path, {"opt_display_smoke_gate_passed": False, "true8h_validation_started": False})
    assert "opt_display_gate_failed" in readiness["blocking_issues"]
