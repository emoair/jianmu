from jianmu.self_learning.darwinforge.extended_bridge_scale_validation import run_extended_bridge_scale_validation


def test_extended_bridge_scale_validation(tmp_path):
    result = run_extended_bridge_scale_validation(
        tmp_path,
        targets={"arithmetic": 1, "function": 1, "array": 1, "function_array": 1, "structured_recursion": 1, "mixed_extended": 1},
        wall_clock_min_hours=0,
        max_runtime_hours=0.01,
        hard_stop_hours=0.02,
        minimum_real_compiler_invocations=1,
    )
    assert result["phase_b_started"] is True
    assert result["all_policy_categories_represented"] is True
    assert result["cached_result_used_as_new_count"] == 0
    assert result["stubbed_validation_detected"] is False

