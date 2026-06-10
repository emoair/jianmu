from jianmu.self_learning.darwinforge.dry_run_execution_harness import _execution_metrics


def test_dry_run_execution_records_policy_path():
    rows = [
        {
            "dry_run_sample_id": "v1_0_6_function_00000001",
            "passed": True,
        }
    ]
    metrics = _execution_metrics(rows, {"function": 1}, {"function": 1}, 0.0, 0.0, False, type("B", (), {"backend_type": "real_c_compiler", "compiler_name": "cl"})(), type("C", (), {"workers": 16})(), 16)
    assert metrics["function_dry_run_success_rate"] == 1.0
    assert metrics["all_policy_categories_represented"] is True
