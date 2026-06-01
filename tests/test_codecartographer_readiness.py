from __future__ import annotations

from jianmu.self_learning.darwinforge.codecartographer_readiness import STILL_NOT_PROVEN, build_codecartographer_readiness, build_codecartographer_training_metrics


def test_readiness_no_arbitrary_project_parser_claim(tmp_path):
    training = build_codecartographer_training_metrics(tmp_path)
    result = build_codecartographer_readiness(
        {"codecartographer_dataset_generated": True},
        {"audit_passed": True, "feature_classification_correctness_rate": 1.0, "standard_token_generation_correctness_rate": 1.0},
        {"leakage_audit_passed": True},
        {"redqueen_targeted_assignment_completed": True},
        {"project_module_challenge_completed": True, "project_module_challenge_passed": True},
        {"module_to_token_success_rate": 0.992, "token_to_ir_success_rate": 0.986},
        {"compiler_verified_correctness_rate": 1.0, "wrong_stdout_count": 0, "timeout_count": 0, "permission_error_count": 0, "cleanup_failure_count": 0, "boundary_compiler_misroute_count": 0, "future_domain_compiled_count": 0},
        training,
        {"charter_guard_passed": True},
        tmp_path,
    )
    assert result["recommended_claim_level"] == "codecartographer_module_to_standardtoken_teacher_positive"
    assert "arbitrary project parsing" in result["still_not_proven"]
    assert "arbitrary project parsing" in STILL_NOT_PROVEN
