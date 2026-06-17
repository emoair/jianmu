from jianmu.self_learning.darwinforge.coverage_expansion_accounting import audit_coverage_expansion_accounting


def test_coverage_expansion_accounting_detects_shape_duplicates(tmp_path):
    rows = [
        {"compile_invocation_id": "a", "compiler_invoked": True, "source_sha256": "s", "shape_signature": "shape", "cached": False, "stubbed": False, "expected_stdout": "1", "actual_stdout": "1"},
        {"compile_invocation_id": "b", "compiler_invoked": True, "source_sha256": "s", "shape_signature": "shape", "cached": False, "stubbed": False, "expected_stdout": "1", "actual_stdout": "1"},
    ]
    result = audit_coverage_expansion_accounting(tmp_path, rows)
    assert result["unique_compile_unit_count"] == 1
    assert result["shape_signature_unique_count"] == 1
