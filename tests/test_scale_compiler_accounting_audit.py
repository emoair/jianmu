from jianmu.self_learning.darwinforge.scale_compiler_accounting_audit import audit_scale_compiler_accounting


def test_scale_compiler_accounting_detects_cached_as_new(tmp_path):
    result = audit_scale_compiler_accounting(tmp_path, [{"compile_invocation_id": "a", "source_sha256": "s", "cached": True, "stubbed": False}])
    assert result["cached_result_used_as_new_count"] == 1


def test_scale_compiler_accounting_detects_stubbed_validation(tmp_path):
    result = audit_scale_compiler_accounting(tmp_path, [{"compile_invocation_id": "a", "source_sha256": "s", "cached": False, "stubbed": True}])
    assert result["stubbed_validation_detected"] is True

