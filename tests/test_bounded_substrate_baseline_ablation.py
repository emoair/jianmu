from __future__ import annotations

from jianmu.self_learning.darwinforge.bounded_substrate_baseline_ablation import run_baseline_ablation


def test_bounded_substrate_baseline_ablation_outputs() -> None:
    result = run_baseline_ablation([{"id": "a", "category": "current_supported_turing_substrate"}], 0.8)
    assert result["baseline_gap_verified"]
    assert "random_router" in result["variants"]
