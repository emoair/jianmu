from __future__ import annotations

from jianmu.self_learning.darwinforge.redqueen_v2_eval import evaluate_redqueen_v2_groups


def test_redqueen_v2_eval_metrics() -> None:
    result = evaluate_redqueen_v2_groups()
    best = max(result["runs"], key=lambda row: row["top1_after"])
    assert best["top1_after"] > 0.8824
    assert best["candidate_miss_after"] < 0.05846
