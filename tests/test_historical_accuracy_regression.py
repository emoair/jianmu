from jianmu.self_learning.darwinforge.historical_accuracy_regression import build_historical_accuracy_regression


def test_historical_accuracy_regression_table(tmp_path):
    eval_metrics = {"profiles": [{"profile_name": "layerwise_sparse_1B_freeze_prune_dryrun_default", "candidate_miss_rate": 0.1, "top1_correct_rate": 0.83, "heldout_supported_success_rate": 0.83, "boundary_false_accept_rate": 0.0}]}
    result = build_historical_accuracy_regression(tmp_path, tmp_path, eval_metrics, {"compiler_verified_correct_rate": 1.0})
    assert result["historical_regression_gate_passed"] is True
    assert len(result["rows"]) >= 5
