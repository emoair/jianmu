from __future__ import annotations

import json

from jianmu.self_learning.darwinforge.bounded_substrate_beam_sweep import run_beam_sweep


def _row(idx: int, split: str = "heldout", category: str = "current_supported_turing_substrate") -> dict:
    return {
        "id": f"{split}-{category}-{idx}",
        "split": split,
        "stage": "variable_declaration",
        "category": category,
        "input": "x",
        "canonical_program": "x",
        "language_features": {},
        "complexity": {},
        "expected_output": "1" if category == "current_supported_turing_substrate" else None,
    }


def test_beam_sweep_outputs_required_beam_sizes(tmp_path) -> None:
    large = tmp_path / "dataset" / "large" / "heldout"
    large.mkdir(parents=True)
    rows = [_row(i) for i in range(20)] + [_row(100 + i, category="unsupported_program_boundary") for i in range(10)]
    (large / "data.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    result = run_beam_sweep(tmp_path / "dataset", tmp_path / "src", tmp_path / "out", [4, 8, 16, 32], 10, 5)
    assert result["beam_sizes_tested"] == [4, 8, 16, 32]


def test_beam_sweep_does_not_change_main_claim(tmp_path) -> None:
    large = tmp_path / "dataset" / "large" / "heldout"
    large.mkdir(parents=True)
    (large / "data.jsonl").write_text(json.dumps(_row(1)) + "\n", encoding="utf-8")
    result = run_beam_sweep(tmp_path / "dataset", tmp_path / "src", tmp_path / "out", [4])
    assert result["diagnostic_only_not_training_gain"] is True

