from __future__ import annotations

from jianmu.self_learning.darwinforge.tree_access_heatmap import run_tree_access_heatmap
from jianmu.self_learning.darwinforge.tree_state_allocation_audit import run_tree_state_allocation_audit


def test_tree_access_heatmap_outputs_layer_stage_matrix(tmp_path) -> None:
    allocation = run_tree_state_allocation_audit("records/v0_9_12", tmp_path)
    heatmap = run_tree_access_heatmap(tmp_path, allocation)
    assert heatmap["tree_access_heatmap_completed"] is True
    assert "if_else_basic" in heatmap["layer_x_stage"]["if_else_branch"]
    assert "state_1B" in heatmap["layer_x_profile"]["candidate_fragment_leaf"]
