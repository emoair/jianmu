from jianmu.self_learning.darwinforge.dataset_backend6h_readiness import build_dataset_backend6h_readiness


def test_backend6h_validation_runner_requires_calibrated_threshold(tmp_path) -> None:
    result = build_dataset_backend6h_readiness(tmp_path, {
        "threshold_calibration_passed": False,
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
    })
    assert "threshold_calibration_failed" in result["blocking_issues"]
    assert result["recommended_claim_level"] == "failed"
