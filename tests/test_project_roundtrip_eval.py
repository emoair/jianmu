from __future__ import annotations

from jianmu.self_learning.darwinforge.project_dataset_builder import build_project_row
from jianmu.self_learning.darwinforge.project_roundtrip_eval import roundtrip_eval


def test_project_roundtrip_eval_works() -> None:
    rows = [build_project_row("pilot", i) for i in range(100)]
    metrics = roundtrip_eval(rows)
    assert metrics["token_to_ir_success_rate"] >= 0.95

