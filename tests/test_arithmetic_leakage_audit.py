import json
from pathlib import Path

from jianmu.self_learning.darwinforge.arithmetic_leakage_audit import audit_arithmetic_leakage


def _row(i, split, category="current_supported_arithmetic"):
    supported = category == "current_supported_arithmetic"
    return {
        "id": f"{split}-{i}",
        "split": split,
        "category": category,
        "stage": "precedence",
        "input": f"{split}:{i}+1",
        "expected_output": f"{i + 1}\n" if supported else None,
        "expression_group_id": f"eg-{split}-{i}",
        "paraphrase_group_id": f"pg-{split}-{i}",
        "target_group_id": f"tg-{split}-{i}" if supported else None,
    }


def _dataset(root: Path):
    for split in ["train", "eval", "test", "heldout"]:
        path = root / "small" / split
        path.mkdir(parents=True, exist_ok=True)
        rows = [_row(i, split) for i in range(60)] + [_row(100 + i, split, "hard_ood") for i in range(10)]
        (path / f"{split}_000.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_leakage_audit_checks_forbidden_and_group_separation(tmp_path):
    records = tmp_path / "records"
    records.mkdir()
    (records / "arithmetic_training_metrics.json").write_text(json.dumps({"forbidden_field_access_count": 0}), encoding="utf-8")
    dataset = tmp_path / "dataset"
    _dataset(dataset)
    result = audit_arithmetic_leakage(records, dataset, tmp_path / "out")
    assert result["target_ir_access_before_candidate_generation"] is False
    assert result["expected_output_access_before_candidate_generation"] is False
    assert result["heldout_train_group_leakage_count"] == 0
