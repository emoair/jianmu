from __future__ import annotations

from jianmu.self_learning.darwinforge.codecartographer_supported_subset import classify_supported_subset


def test_supported_subset_blocks_recursion_pointer_io():
    result = classify_supported_subset({"has_recursion": True, "has_pointer": True, "has_io": True})
    assert result["support_status"] == "unsupported"
    assert result["expected_action"] == "reject"
    assert result["unsupported_feature_isolation_correct"] is True
