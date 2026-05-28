from __future__ import annotations

import json

from jianmu.self_learning.darwinforge.bounded_substrate_candidate_error_taxonomy import classify_candidate_error, run_candidate_error_taxonomy


def test_candidate_error_taxonomy_classifies_candidate_miss() -> None:
    assert classify_candidate_error({"category": "current_supported_turing_substrate", "candidate_hit": False}) == "candidate_miss"


def test_candidate_error_taxonomy_classifies_in_beam_wrong_top1() -> None:
    row = {"category": "current_supported_turing_substrate", "candidate_hit": True, "correct_output_in_beam": True, "top1_correct": False}
    assert classify_candidate_error(row) == "candidate_in_beam_but_wrong_top1"


def test_candidate_error_taxonomy_writes_outputs(tmp_path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "heldout_freebeam_trace.jsonl").write_text(json.dumps({"sample_id_hash": "a", "stage": "variable_declaration", "category": "current_supported_turing_substrate", "candidate_hit": False}) + "\n", encoding="utf-8")
    result = run_candidate_error_taxonomy(src, tmp_path / "out")
    assert result["candidate_error_taxonomy_completed"] is True
    assert (tmp_path / "out" / "candidate_error_taxonomy.json").exists()

