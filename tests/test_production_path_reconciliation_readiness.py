from jianmu.self_learning.darwinforge.production_path_reconciliation_readiness import build_production_path_reconciliation_readiness


def test_no_production_promotion(tmp_path):
    result = _readiness(tmp_path)
    assert result["production_function_support_completed"] is False
    assert result["production_array_support_completed"] is False
    assert result["production_recursion_support_completed"] is False
    assert result["real_promotion_disabled"] is True


def test_ready_for_official_release_false(tmp_path):
    result = _readiness(tmp_path)
    assert result["ready_for_official_release"] is False


def _readiness(tmp_path):
    validation = {"compiler_verified_correctness_rate": 1.0, "wrong_stdout": 0, "timeout": 0, "stubbed_validation_detected": False, "summary_only_validation_detected": False}
    trace_pack = {"evidence_trace_pack_generated": True, "blocking_issues": ["raw_trace_missing"], "raw_trace_available_in_v1_package": False, "raw_trace_available_in_current_workspace": True}
    metric = {"metric_provenance_completed": True, "fixed_metric_scaffold_count": 1}
    claim = {"claim_boundary_fix_completed": True, "production_function_support_completed": False}
    return build_production_path_reconciliation_readiness(tmp_path, validation, trace_pack, metric, claim)

