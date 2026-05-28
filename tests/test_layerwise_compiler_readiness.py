from jianmu.self_learning.darwinforge.layerwise_compiler_readiness import build_layerwise_compiler_readiness


def test_layerwise_readiness_no_profile_promotion_claim(tmp_path):
    readiness = build_layerwise_compiler_readiness(
        tmp_path,
        {"taxonomy_completed": True, "original_failure_count": 1, "classified_failure_count": 1, "dominant_failure_category": "cl_or_link_toolchain_error", "engineering_issue_dominant": True},
        {"failure_replay_completed": True},
        {"clean_rerun_completed": True, "best_run_label": "primary_16", "runs": {"primary_16": {"completed": True, "compiler_verified_correct_rate": 1.0, "permission_error_count": 0, "cleanup_failure_count": 0, "boundary_compiler_misroute_count": 0, "future_domain_compiled_count": 0, "recursion_compiled_count": 0, "array_compiled_count": 0, "function_compiled_count": 0, "backend_claim_safe": True}}},
        {"mandatory_counter_guard_passed": True, "original_v0_9_12_2_result_preserved": True},
    )
    assert readiness["recommended_claim_level"] == "layerwise_compiler_validation_restored"
    assert "profile promotion completed" not in str(readiness).lower()


def test_layerwise_readiness_no_turing_complete_claim(tmp_path):
    readiness = build_layerwise_compiler_readiness(tmp_path, {}, {}, {"runs": {}, "best_run_label": ""}, {"mandatory_counter_guard_passed": True})
    assert "turing" not in readiness["recommended_claim_level"].lower()
