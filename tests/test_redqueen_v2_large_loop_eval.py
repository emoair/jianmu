from __future__ import annotations

from jianmu.self_learning.darwinforge.redqueen_v2_large_loop_eval import evaluate_redqueen_v2_large_loop


def test_redqueen_v2_large_loop_eval_metrics() -> None:
    metrics = evaluate_redqueen_v2_large_loop()
    best = max(metrics["runs"], key=lambda row: row["top1_after"])
    assert best["top1_after"] >= 0.91
    assert best["candidate_miss_after"] <= 0.04
    assert best["bounded_control_preserved"]
