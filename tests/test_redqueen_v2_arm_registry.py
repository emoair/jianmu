from __future__ import annotations

from jianmu.self_learning.darwinforge.redqueen_v2_arm_registry import build_arm_registry


def test_redqueen_v2_arm_registry() -> None:
    registry = build_arm_registry()
    assert registry["arm_count"] == 11
    assert all(not row["eligible_for_runtime_boundary"] for row in registry["arms"])
