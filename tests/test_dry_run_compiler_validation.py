from jianmu.self_learning.darwinforge.dry_run_compiler_validation import audit_dry_run_compiler_accounting, detect_stubbed_validation


def test_dry_run_compiler_validation_detects_stubbed_validation(tmp_path):
    rows = [{"compile_invocation_id": "a", "passed": True, "exe_run": False, "stubbed": True, "cached": False, "expected_stdout": "1", "actual_stdout": "1"}]
    result = audit_dry_run_compiler_accounting(tmp_path, rows)
    assert result["stubbed_validation_detected"] is True
    assert detect_stubbed_validation(rows) is True
