from __future__ import annotations

from jianmu.self_learning.darwinforge.dataset_activation_audit import run_dataset_activation_audit
from jianmu.self_learning.darwinforge.tree_allocation_failure_analysis import write_tree_allocation_failure_analysis
from jianmu.self_learning.darwinforge.tree_state_allocation_audit import run_tree_state_allocation_audit


def test_tree_allocation_failure_analysis_outputs_examples(tmp_path) -> None:
    allocation = run_tree_state_allocation_audit("records/v0_9_12", tmp_path)
    dataset = run_dataset_activation_audit("datasets/v0_9_9_turing_frontier_curriculum", "datasets/v0_9_6_turing_substrate_curriculum", "records/v0_9_12", tmp_path)
    result = write_tree_allocation_failure_analysis(tmp_path, allocation, dataset)
    assert result["failure_analysis_completed"] is True
    assert (tmp_path / "tree_allocation_failure_examples.jsonl").exists()
