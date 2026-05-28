from __future__ import annotations

from jianmu.self_learning.darwinforge.state_budget_failure_analysis import write_state_budget_failure_analysis


def test_state_budget_failure_analysis_outputs_examples(tmp_path) -> None:
    write_state_budget_failure_analysis(tmp_path, [{"profile_name": "state_10M", "candidate_miss_rate": 0.2, "materialization_level": "fully_materialized"}])
    assert (tmp_path / "state_budget_failure_examples.jsonl").read_text(encoding="utf-8")

