from jianmu.self_learning.darwinforge.csystems_frontier_core import build_csystems_row
from jianmu.self_learning.darwinforge.csystems_memory_contract_audit import memory_contract_audit


def test_malloc_patterns_lifecycle_contract():
    row = build_csystems_row(20)
    assert row["feature_family"] == "malloc_frontier"
    assert row["memory_contract"]["allocation_failure_branch_present"] is True
    assert row["memory_contract"]["free_count_matches_alloc_count"] is True


def test_memory_contract_detects_missing_free():
    row = build_csystems_row(20)
    row["memory_contract"]["leak_contract_violation"] = True
    result = memory_contract_audit([row])
    assert result["leak_contract_violation_count"] == 1


def test_memory_contract_detects_double_free():
    row = build_csystems_row(20)
    row["memory_contract"]["double_free_detected"] = True
    result = memory_contract_audit([row])
    assert result["double_free_detected_count"] == 1
