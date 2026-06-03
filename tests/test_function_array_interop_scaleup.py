from jianmu.self_learning.darwinforge.function_array_interop_scaleup import run_function_array_interop


def test_function_array_interop(tmp_path):
    result = run_function_array_interop(tmp_path)
    assert result["function_array_combined_success_rate"] >= 0.86
    assert result["array_pass_to_function_success_rate"] >= 0.85
    assert result["function_array_interop_positive"] is True
