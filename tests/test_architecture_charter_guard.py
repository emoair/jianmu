from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.architecture_charter_guard import run_architecture_charter_guard


def test_architecture_charter_exists() -> None:
    assert Path("docs/architecture/JIANMU_ARCHITECTURE_CHARTER.md").exists()


def test_boundary_as_data_contract_documented() -> None:
    result = run_architecture_charter_guard(".")
    assert result["boundary_as_data_contract_documented"] is True


def test_no_runtime_keyword_rejection_gate_added() -> None:
    result = run_architecture_charter_guard(".")
    assert result["no_runtime_keyword_rejection_gate_added"] is True


def test_no_candidate_generation_boundary_hardcode_added() -> None:
    result = run_architecture_charter_guard(".")
    assert result["no_candidate_generation_boundary_hardcode_added"] is True


def test_regression_dashboard_not_replay_buffer() -> None:
    result = run_architecture_charter_guard(".")
    assert result["regression_dashboard_not_replay_buffer"] is True
