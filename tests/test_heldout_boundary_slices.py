import json

from jianmu.self_learning.darwinforge.heldout_boundary_slices import build_heldout_boundary_slices


def _write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_heldout_boundary_slices_no_input_leakage(tmp_path):
    _write_jsonl(tmp_path / "train.jsonl", [{"sample_id": "tr", "raw_text": "a", "boundary_label": "current_supported"}])
    _write_jsonl(tmp_path / "eval_ood_boundary.jsonl", [{"sample_id": "ev", "raw_text": "b", "boundary_label": "hard_ood"}])
    result = build_heldout_boundary_slices(tmp_path)
    assert result["leakage_check_passed"] is True


def test_heldout_boundary_slices_no_paraphrase_leakage(tmp_path):
    _write_jsonl(tmp_path / "train.jsonl", [{"sample_id": "tr", "raw_text": "a", "paraphrase_group_id": "pg1", "boundary_label": "current_supported"}])
    _write_jsonl(tmp_path / "eval_ood_boundary.jsonl", [{"sample_id": "ev", "raw_text": "b", "paraphrase_group_id": "pg2", "boundary_label": "hard_ood"}])
    result = build_heldout_boundary_slices(tmp_path)
    assert not result["leakage_issues"]
