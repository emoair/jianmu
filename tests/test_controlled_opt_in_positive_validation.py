from jianmu.self_learning.darwinforge.controlled_opt_in_positive_validation import _metrics
from jianmu.self_learning.darwinforge.controlled_opt_in_support_schema import ControlledOptInSupportConfig


def test_positive_validation_requires_compiler_correctness():
    rows = []
    for category in ["function", "array", "function_array", "structured_recursion", "mixed", "opt_in_rollback", "replay_sample"]:
        rows.append({"category": category, "passed": True, "compiler_invoked": category not in {"opt_in_rollback", "replay_sample"}, "expected_stdout": "1", "actual_stdout": "1", "timeout": False, "permission_error": False, "cleanup_failure": False, "cached": False, "stubbed": False, "compile_invocation_id": category})
    result = _metrics(rows, ControlledOptInSupportConfig(positive_validation_events=7, minimum_real_compiler_invocations=5))
    assert result["positive_validation_passed"] is True


def test_no_external_api_calls():
    import pathlib

    text = pathlib.Path("jianmu/self_learning/darwinforge/controlled_opt_in_positive_validation.py").read_text(encoding="utf-8")
    assert "openai" not in text.lower()
    assert "requests." not in text


def test_real_promotion_disabled():
    import pathlib

    text = pathlib.Path("jianmu/self_learning/darwinforge/controlled_opt_in_support_readiness.py").read_text(encoding="utf-8")
    assert '"real_promotion_enabled": True' not in text
