from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.redqueen_autopsy import load_inputs
from jianmu.self_learning.darwinforge.redqueen_regression_sentinel import run_redqueen_regression_sentinel


def test_regression_sentinel_not_replay_buffer() -> None:
    data = load_inputs("records/v0_9_17", "records/v0_9_18", "records/v0_9_18_2", "datasets/v0_9_17_redqueen_curriculum")
    result = run_redqueen_regression_sentinel(data)
    assert result["sentinel_passed"] is True
    text = Path("jianmu/self_learning/darwinforge/redqueen_regression_sentinel.py").read_text(encoding="utf-8").lower()
    assert "replay_buffer" not in text
