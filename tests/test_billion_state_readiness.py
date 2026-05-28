from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.billion_state_readiness import build_billion_state_readiness


def test_readiness_no_turing_complete_claim(tmp_path) -> None:
    best = {"profile_name": "state_1B", "target_state_units": 1_000_000_000, "actual_state_units_allocated": 1_000_000_000, "materialization_level": "lazy_indexed", "candidate_miss_rate": 0.13, "top1_correct_rate": 0.79, "heldout_supported_success_rate": 0.79, "boundary_false_accept_rate": 0.0, "future_domain_supported_accept_rate": 0.0}
    ref = {"candidate_miss_rate": 0.1666, "top1_correct_rate": 0.76864}
    access = {"access_audit_completed": True, "profiles": [{"profile_name": "state_1B", "materialization_level": "lazy_indexed", "touch_ratio": 0.052, "whether_1B_budget_was_substantively_used": True}]}
    scaling = {"capacity_threshold_signal_detected": False, "sharp_transition_detected": False, "smooth_scaling_detected": True, "diminishing_returns_detected": True, "saturation_detected": True}
    compiler = {"compiler_validation_completed": True, "per_profile": {"state_1B": {"compiler_verified_correct_rate": 1.0, "boundary_compiler_misroute_count": 0}}}
    result = build_billion_state_readiness(tmp_path, ["state_1B"], ["state_1B"], {}, best, ref, access, scaling, compiler, {"forbidden_field_access_count": 0}, True, True)
    assert result["recommended_claim_level"] == "billion_state_budget_probe_positive"
    text = (tmp_path / "billion_state_readiness.json").read_text(encoding="utf-8").lower()
    assert "turing complete" not in text


def test_integrity_no_forbidden_fields() -> None:
    text = Path("jianmu/self_learning/darwinforge/billion_state_scale_probe.py").read_text(encoding="utf-8")
    assert '"forbidden_field_access_count": 0' in text


def test_no_expression_oracle_import() -> None:
    text = Path("jianmu/self_learning/darwinforge/billion_state_scale_probe.py").read_text(encoding="utf-8")
    assert "expression_oracle" not in text


def test_no_external_api_calls() -> None:
    text = Path("jianmu/self_learning/darwinforge/billion_state_scale_probe.py").read_text(encoding="utf-8").lower()
    assert "openai" not in text
    assert "requests." not in text


def test_no_hardcoded_keyword_gate() -> None:
    text = Path("jianmu/self_learning/darwinforge/billion_state_eval.py").read_text(encoding="utf-8").lower()
    assert "keyword gate" not in text


def test_real_promotion_disabled() -> None:
    text = Path("docs/experiments/BILLION_STATE_BUDGET_UPPER_FRONTIER_PROBE.md").read_text(encoding="utf-8").lower()
    assert "safe real promotion" in text

