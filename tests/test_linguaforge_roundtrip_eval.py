from __future__ import annotations

from jianmu.self_learning.darwinforge.linguaforge_nl_schema import build_linguaforge_row
from jianmu.self_learning.darwinforge.linguaforge_roundtrip_eval import evaluate_roundtrip


def test_linguaforge_roundtrip_eval_indirect_success() -> None:
    rows = [build_linguaforge_row("pilot", i) for i in range(40)]
    metrics = evaluate_roundtrip(rows)
    assert metrics["token_to_ir_success_rate"] >= 0.95
    assert metrics["roundtrip_success_rate"] >= 0.95

