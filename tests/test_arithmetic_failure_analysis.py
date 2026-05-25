import json
from pathlib import Path

from jianmu.self_learning.darwinforge.arithmetic_failure_analysis import run_targeted_arithmetic_rerun


def _row(i, split, stage="precedence", category="current_supported_arithmetic"):
    return {
        "id": f"{split}-{stage}-{i}",
        "split": split,
        "category": category,
        "stage": stage,
        "input": f"{i}+1",
        "expected_output": f"{i + 1}\n" if category == "current_supported_arithmetic" else None,
    }


def _dataset(root: Path):
    train = root / "small" / "train"
    train.mkdir(parents=True, exist_ok=True)
    stages = ["precedence", "parentheses", "negative_numbers", "exact_division"]
    rows = [_row(i, "train", stages[i % len(stages)]) for i in range(80)]
    rows += [_row(100 + i, "train", "division_boundary", "unsupported_arithmetic_boundary") for i in range(10)]
    (train / "train_000.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    for split in ["eval", "test", "heldout"]:
        path = root / "small" / split
        path.mkdir(parents=True, exist_ok=True)
        (path / f"{split}_000.jsonl").write_text("".join(json.dumps(_row(i, split, "boundary", "hard_ood")) + "\n" for i in range(10)), encoding="utf-8")


def test_failure_analysis_targeted_rerun_outputs_samples(tmp_path):
    dataset = tmp_path / "dataset"
    _dataset(dataset)
    result = run_targeted_arithmetic_rerun(dataset, tmp_path / "out", heldout_samples=40, boundary_samples=20)
    assert result["targeted_rerun_completed"] is True
    assert result["candidate_hit_after"] > result["candidate_hit_before"]
    assert (tmp_path / "out" / "failure_examples.jsonl").exists()
