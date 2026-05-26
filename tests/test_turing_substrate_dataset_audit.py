from __future__ import annotations

import json
from pathlib import Path

from jianmu.self_learning.darwinforge.turing_substrate_dataset_audit import audit_turing_substrate_dataset


def test_turing_substrate_audit_blocks_leakage(tmp_path: Path) -> None:
    split = tmp_path / "train"
    split.mkdir(parents=True)
    for other in ["eval", "test", "heldout"]:
        (tmp_path / other).mkdir()
    row = {
        "id": "x",
        "split": "train",
        "category": "unsupported_program_boundary",
        "stage": "boundary",
        "input": "same",
        "canonical_program": None,
        "target_ir": {"op": "Program"},
        "expected_output": None,
        "language_features": {},
        "compiler_expectation": {},
    }
    (split / "train_000.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    audit = audit_turing_substrate_dataset(tmp_path)
    assert audit["non_supported_has_targetir_count"] == 1
    assert not audit["audit_passed"]
