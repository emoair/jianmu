import json

from jianmu.self_learning.darwinforge.train_heldout_split_guard import run_train_heldout_split_guard


def test_train_heldout_split_guard_detects_overlap(tmp_path) -> None:
    manifest = tmp_path / "manifest"
    manifest.mkdir()
    rows = [
        {"sample_id": "a", "sha256": "same", "split": "train", "category": "arithmetic"},
        {"sample_id": "b", "sha256": "same", "split": "heldout", "category": "arithmetic"},
    ]
    (manifest / "x.jsonl").write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    result = run_train_heldout_split_guard(tmp_path, manifest)
    assert result["leakage_detected"] is True
    assert result["split_guard_passed"] is False
