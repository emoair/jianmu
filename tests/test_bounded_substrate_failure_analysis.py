from __future__ import annotations

from jianmu.self_learning.darwinforge.bounded_substrate_failure_analysis import write_failure_analysis


def test_mainline_conclusion_ledger_exists(tmp_path) -> None:
    summary = write_failure_analysis(tmp_path, [{"category": "current_supported_turing_substrate", "candidate_hit": False, "sample_id_hash": "x"}], {})
    assert summary["candidate_miss"] == 1
    assert (tmp_path / "failure_analysis.md").exists()
