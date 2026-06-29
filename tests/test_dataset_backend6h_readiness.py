from jianmu.self_learning.darwinforge.dataset_backend6h_readiness import build_dataset_backend6h_readiness


def test_dataset_backend6h_readiness_keeps_production_false(tmp_path) -> None:
    payload = {
        "threshold_calibration_passed": True,
        "dataset_training_passed": True,
        "split_guard_passed": True,
        "redqueen_dataset_scheduler_passed": True,
        "mirror_feedback_passed": True,
        "backend6h_validation_passed": True,
        "dataset_evidence_pack_passed": True,
        "repo_hygiene_guard_passed": True,
        "trace_shard_size_cap_passed": True,
        "memory_guard_passed": True,
        "lifecycle_guard_passed": True,
    }
    result = build_dataset_backend6h_readiness(tmp_path, payload)
    assert result["production_function_support_completed"] is False
    assert result["real_promotion_enabled"] is False
    assert result["recommended_claim_level"] == "active_work_calibrated_dataset_training_backend6h_positive"
