from jianmu.self_learning.darwinforge.turing_frontier_regression_guard import write_turing_frontier_regression_guard


def test_turing_frontier_regression_guard(tmp_path):
    result = write_turing_frontier_regression_guard(tmp_path, {"terminating_unbounded_success_rate": 0.939, "recursion_success_rate": 0.918, "state_growth_success_rate": 0.92, "counter_machine_witness_success_rate": 0.976})
    assert result["regression_clean"] is True
    assert not result["blocking_regressions"]
