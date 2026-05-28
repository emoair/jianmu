from __future__ import annotations

import json

from jianmu.self_learning.darwinforge.targeted_candidate_space_failure_analysis import write_targeted_failure_analysis


def test_targeted_failure_analysis_writes_taxonomy(tmp_path) -> None:
    taxonomy = {"dominant_failure_type": "candidate_miss", "candidate_miss_count": 3}
    write_targeted_failure_analysis(tmp_path, taxonomy, [{"sample_id_hash": "abc", "failure_type": "candidate_miss"}])
    saved = json.loads((tmp_path / "targeted_candidate_error_taxonomy.json").read_text(encoding="utf-8"))
    assert saved["dominant_failure_type"] == "candidate_miss"
    assert (tmp_path / "targeted_candidate_examples.jsonl").exists()

