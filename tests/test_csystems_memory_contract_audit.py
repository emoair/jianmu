from jianmu.self_learning.darwinforge.csystems_frontier_core import build_csystems_row, memory_contract_audit


def test_csystems_memory_contract_audit():
    result = memory_contract_audit([build_csystems_row(20)])
    assert result["memory_contract_passed"] is True
    assert result["use_after_free_detected_count"] == 0
