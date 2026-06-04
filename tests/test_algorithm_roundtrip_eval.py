from __future__ import annotations

from jianmu.self_learning.darwinforge.algorithm_roundtrip_eval import roundtrip_metrics
from jianmu.self_learning.darwinforge.forgecorpus_algorithm_schema import build_algorithm_row


def test_algorithm_roundtrip_eval() -> None:
    rows = [build_algorithm_row("pilot", i) for i in range(100)]
    assert roundtrip_metrics(rows)["token_to_ir_success_rate"] >= 0.95

