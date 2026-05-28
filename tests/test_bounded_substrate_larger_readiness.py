from __future__ import annotations

from pathlib import Path


from jianmu.self_learning.darwinforge.bounded_substrate_larger_readiness import assess_larger_readiness


def _base_metrics() -> dict:
    return {
        "larger_rerun_completed": True,
        "larger_rerun_partial": False,
        "dataset_scales_used": ["small"],
        "seeds_completed": [63],
        "forbidden_field_access_count": 0,
        "expected_output_access_before_candidate_generation": False,
        "target_ir_access_before_candidate_generation": False,
        "supported_candidate_hit_before": 0.2,
        "supported_candidate_hit_after": 0.4,
        "top1_supported_correct_before": 0.1,
        "top1_supported_correct_after": 0.4,
        "heldout_supported_success_rate": 0.5,
        "compiler_validation_completed": True,
        "backend_type": "real_c_compiler",
        "compiler_name": "cl",
        "compile_worker_count": 16,
        "compiler_verified_correct_rate": 1.0,
        "permission_error_count": 0,
        "cleanup_failure_count": 0,
        "boundary_compiler_misroute_count": 0,
        "cross_process_reload_passed": True,
        "persisted_state_support_level": "full_router_root",
        "baseline_gap_verified": True,
        "synthetic_summary_detected": False,
        "fixed_metric_detected": False,
        "periodic_rule_detected": False,
    }


def test_bounded_substrate_larger_readiness_no_turing_complete_claim() -> None:
    readiness = assess_larger_readiness(_base_metrics(), {"progress_enabled": True, "metrics_affected_by_progress": False})
    assert readiness["recommended_claim_level"] == "bounded_substrate_larger_positive_signal"
    assert "Turing" not in readiness["recommended_claim_level"]


def test_no_expression_oracle_import() -> None:
    text = Path("jianmu/self_learning/darwinforge/bounded_substrate_larger_readiness.py").read_text(encoding="utf-8")
    assert "expression_oracle" not in text


def test_no_external_api_calls() -> None:
    text = Path("jianmu/self_learning/darwinforge/bounded_substrate_larger_training_runner.py").read_text(encoding="utf-8").lower()
    assert "openai" not in text
    assert "requests." not in text


def test_no_hardcoded_keyword_gate() -> None:
    text = Path("jianmu/self_learning/darwinforge/bounded_substrate_larger_training_runner.py").read_text(encoding="utf-8").lower()
    assert "keyword gate" not in text


def test_real_promotion_disabled() -> None:
    text = Path("docs/experiments/BOUNDED_SUBSTRATE_LARGER_TRAINING_RERUN.md").read_text(encoding="utf-8").lower()
    assert "real promotion" in text
    assert "safe real promotion" in text

