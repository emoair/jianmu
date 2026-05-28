from __future__ import annotations

import json

from jianmu.self_learning.darwinforge.bounded_substrate_larger_failure_analysis import write_larger_failure_analysis


def test_larger_failure_analysis_writes_expected_files(tmp_path) -> None:
    summary = write_larger_failure_analysis(
        tmp_path,
        [{"sample_id_hash": "a", "category": "current_supported_turing_substrate", "candidate_hit": False, "stage": "if_else_basic"}],
        {"compile_failure_count": 0, "runtime_failure_count": 0},
    )
    assert summary["failure_category_counts"]["candidate_miss"] == 1
    assert (tmp_path / "failure_analysis.md").exists()
    rows = [json.loads(line) for line in (tmp_path / "failure_examples.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows[0]["failure_category"] == "candidate_miss"

