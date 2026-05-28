from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.state_budget_readiness import build_state_budget_readiness


def test_readiness_no_turing_complete_claim(tmp_path) -> None:
    best = {"profile_name": "state_100M", "target_state_units": 100_000_000, "actual_state_units_allocated": 100_000_000, "materialization_level": "lazy_indexed", "candidate_miss_rate": 0.16, "top1_correct_rate": 0.76, "heldout_supported_success_rate": 0.76, "boundary_false_accept_rate": 0.0, "future_domain_supported_accept_rate": 0.0}
    baseline = {"candidate_miss_rate": 0.2386, "top1_correct_rate": 0.7096}
    compiler = {"compiler_validation_completed": True, "per_profile": {"state_100M": {"compiler_verified_correct_rate": 1.0, "boundary_compiler_misroute_count": 0}}}
    scaling = {"capacity_threshold_signal_detected": True, "sharp_transition_detected": False, "diminishing_returns_detected": True}
    result = build_state_budget_readiness(tmp_path, ["baseline_targeted", "state_100M"], ["baseline_targeted", "state_100M"], {}, best, baseline, scaling, compiler, {"forbidden_field_access_count": 0}, True, True)
    assert result["recommended_claim_level"] == "hundred_million_state_budget_probe_positive"
    text = (tmp_path / "state_budget_readiness.json").read_text(encoding="utf-8").lower()
    assert "turing complete" not in text


def test_integrity_no_forbidden_fields() -> None:
    text = Path("jianmu/self_learning/darwinforge/state_budget_scale_probe.py").read_text(encoding="utf-8")
    assert '"forbidden_field_access_count": 0' in text


def test_no_expression_oracle_import() -> None:
    text = Path("jianmu/self_learning/darwinforge/state_budget_scale_probe.py").read_text(encoding="utf-8")
    assert "expression_oracle" not in text


def test_no_external_api_calls() -> None:
    text = Path("jianmu/self_learning/darwinforge/state_budget_scale_probe.py").read_text(encoding="utf-8").lower()
    assert "openai" not in text
    assert "requests." not in text


def test_no_hardcoded_keyword_gate() -> None:
    text = Path("jianmu/self_learning/darwinforge/state_budget_eval.py").read_text(encoding="utf-8").lower()
    assert "keyword gate" not in text


def test_real_promotion_disabled() -> None:
    text = Path("docs/experiments/HUNDRED_MILLION_STATE_BUDGET_PROBE.md").read_text(encoding="utf-8").lower()
    assert "safe real promotion" in text

