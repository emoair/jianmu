from __future__ import annotations

from jianmu.self_learning.darwinforge.bounded_substrate_training_state import train_bounded_substrate_state, write_full_router_root_state


def test_bounded_substrate_training_state_full_router_root(tmp_path) -> None:
    state = train_bounded_substrate_state([{"category": "current_supported_turing_substrate", "training_usage": "train_current", "stage": "variable_declaration", "nutrient_policy": {"supported_correct": 1.0}}])
    manifest = write_full_router_root_state(state, tmp_path)
    assert manifest["persisted_state_support_level"] == "full_router_root"
    assert manifest["missing_for_full_state"] == []
