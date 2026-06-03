from jianmu.self_learning.darwinforge.function_array_regression_guard import write_function_array_regression_guard


def test_function_array_regression_guard(tmp_path):
    result = write_function_array_regression_guard(tmp_path, {"function_success_rate": 0.929, "array_success_rate": 0.925, "function_array_success_rate": 0.902})
    assert result["regression_clean"] is True
    assert result["metric_deltas"]["function_array_success_rate"] > 0
