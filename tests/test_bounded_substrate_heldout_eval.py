from __future__ import annotations

from jianmu.self_learning.darwinforge.bounded_substrate_heldout_eval import REQUIRED_HELDOUT_STAGES, summarize_heldout


def test_bounded_substrate_heldout_eval_has_required_stages() -> None:
    result = summarize_heldout([])
    assert list(result["by_stage"].keys()) == REQUIRED_HELDOUT_STAGES
