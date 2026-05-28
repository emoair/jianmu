from __future__ import annotations

from jianmu.self_learning.darwinforge.dataset_activation_audit import run_dataset_activation_audit


def test_dataset_activation_audit_detects_underactivation(tmp_path) -> None:
    result = run_dataset_activation_audit(
        "datasets/v0_9_9_turing_frontier_curriculum",
        "datasets/v0_9_6_turing_substrate_curriculum",
        "records/v0_9_12",
        tmp_path,
    )
    assert result["dataset_activation_audit_completed"] is True
    assert result["dataset_underactivation_detected"] is True
    assert result["future_quarantine_coldness_intentional"] is True
    assert result["scales"]["large"]["control_stage_counts"]["bounded_for_loop"] > 0
