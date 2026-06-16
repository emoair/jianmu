from jianmu.self_learning.darwinforge.opt_in_longhaul_accounting import audit_longhaul_accounting


def test_longhaul_accounting_detects_duplicate_invocation_id(tmp_path):
    rows = [
        {"compile_invocation_id": "x", "compiler_invoked": True, "source_sha256": "s", "cached": False, "stubbed": False, "expected_stdout": "1", "actual_stdout": "1"},
        {"compile_invocation_id": "x", "compiler_invoked": True, "source_sha256": "s", "cached": False, "stubbed": False, "expected_stdout": "1", "actual_stdout": "1"},
    ]
    result = audit_longhaul_accounting(tmp_path, rows)
    assert result["duplicate_invocation_id_count"] == 1
