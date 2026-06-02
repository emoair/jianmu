from jianmu.self_learning.darwinforge.turing_frontier_scaleup_metrics import run_scaleup_metrics


def test_scaleup_metrics_outputs_best_group(tmp_path):
    result = run_scaleup_metrics(tmp_path, 12.0, 24)
    best = result["best_window"]
    assert result["best_experiment_group"] == "redqueen_hydrabudget_symbiote_true_endurance"
    assert best["terminating_unbounded_success_rate"] >= 0.93
    assert best["recursion_success_rate"] >= 0.91
    assert best["state_growth_success_rate"] >= 0.91
