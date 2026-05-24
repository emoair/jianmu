from jianmu.self_learning.darwinforge.arithmetic_compiler_spot_audit import run_arithmetic_compiler_spot_audit


def test_arithmetic_compiler_spot_audit_marks_backend_type():
    rows = [{
        "id": "s1",
        "category": "current_supported_arithmetic",
        "target_ir": {"op": "add", "args": [{"op": "int", "value": 1}, {"op": "int", "value": 2}]},
        "expected_output": "3\n",
    }]
    result = run_arithmetic_compiler_spot_audit(rows, mode="quick")
    assert result["compiler_backend_type"] == "internal_evaluator"
    assert result["compiler_eval_call_count"] == 1
