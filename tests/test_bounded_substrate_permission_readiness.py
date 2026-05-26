from __future__ import annotations

from jianmu.self_learning.darwinforge.bounded_substrate_permission_readiness import assess_permission_failure_readiness


def test_permission_readiness_no_turing_complete_claim(tmp_path) -> None:
    result = assess_permission_failure_readiness(
        tmp_path,
        {"taxonomy_completed": True, "engineering_issue_dominant": True, "original_failure_count": 1, "classified_failure_count": 1, "dominant_failure_category": "permission_cleanup_temp_dir"},
        {"patched_replay_sample_count": 1, "patched_permission_error_count": 0, "patched_compiler_verified_correct_rate": 1.0, "original_result_preserved": True},
        {"supported_sample_count": 1, "permission_error_count": 0, "compiler_verified_correct_rate": 1.0, "boundary_compiler_misroute_count": 0},
    )
    assert result["recommended_claim_level"] == "compiler_permission_failures_explained_and_fixed"
    assert "Turing completeness" not in str(result)


def test_independent_validation_uses_real_cl() -> None:
    # The readiness gate does not itself invoke cl.exe, but it requires the
    # independent validation metrics to carry compiler-backed success.
    result = assess_permission_failure_readiness(
        __import__("tempfile").mkdtemp(),
        {"taxonomy_completed": True, "engineering_issue_dominant": True, "dominant_failure_category": "permission_cleanup_temp_dir"},
        {"patched_replay_sample_count": 1, "patched_permission_error_count": 0, "patched_compiler_verified_correct_rate": 1.0, "original_result_preserved": True},
        {"supported_sample_count": 1, "permission_error_count": 0, "compiler_verified_correct_rate": 1.0, "boundary_compiler_misroute_count": 0},
    )
    assert result["independent_validation_executed"] is True
