from __future__ import annotations

import hashlib
from pathlib import Path

from jianmu.self_learning.darwinforge.dataset_balanced_resampling_probe import run_dataset_balanced_resampling_probe


def test_dataset_balanced_resampling_probe_does_not_modify_dataset(tmp_path) -> None:
    dataset_file = next(Path("datasets/v0_9_9_turing_frontier_curriculum/large/train").glob("*.jsonl"))
    before = hashlib.sha256(dataset_file.read_bytes()).hexdigest()
    result = run_dataset_balanced_resampling_probe("records/v0_9_12", tmp_path)
    after = hashlib.sha256(dataset_file.read_bytes()).hexdigest()
    assert before == after
    assert result["dataset_resampling_probe_completed"] is True
    assert result["dataset_resampling_improves_top1"] is True
