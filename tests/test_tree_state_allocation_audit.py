from __future__ import annotations

from jianmu.self_learning.darwinforge.tree_state_allocation_audit import LAYER_ORDER, run_tree_state_allocation_audit


def test_tree_state_allocation_audit_layers(tmp_path) -> None:
    result = run_tree_state_allocation_audit("records/v0_9_12", tmp_path)
    assert result["tree_allocation_audit_completed"] is True
    names = {row["layer_name"] for row in result["layers"]}
    assert set(LAYER_ORDER).issubset(names)
    assert result["intentionally_cold_future_branches"]
    assert all("allocated_units" in row for row in result["layers"])
