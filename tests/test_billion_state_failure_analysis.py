from __future__ import annotations

from jianmu.self_learning.darwinforge.billion_state_failure_analysis import write_billion_state_failure_analysis


def test_billion_state_failure_analysis_outputs_examples(tmp_path) -> None:
    write_billion_state_failure_analysis(tmp_path, [{"profile_name": "state_1B", "candidate_miss_rate": 0.13}], {"profiles": [{"profile_name": "state_1B", "touch_ratio": 0.052}]})
    assert (tmp_path / "billion_state_failure_examples.jsonl").read_text(encoding="utf-8")

