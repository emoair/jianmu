from jianmu.self_learning.darwinforge.v0_9_1_1_readiness import reconcile_v0_9_1_claim


def test_readiness_downgrades_harness_probe_only():
    readiness = reconcile_v0_9_1_claim(
        {"actual_train_iterated_count": 0, "actual_eval_iterated_count": 0, "actual_external_ood_iterated_count": 0, "count_match_passed": False},
        {"cross_process_trace_passed": False, "child_eval_sample_count": 0},
        {"baseline_real_execution_verified": False},
        {"ablation_real_execution_verified": False},
        {"anomaly_severity": "blocking"},
    )
    assert readiness["recommended_claim_level"] == "needs_real_longrun"
    assert readiness["real_xlarge_verified"] is False
