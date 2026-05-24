from jianmu.self_learning.darwinforge.arithmetic_training_state import ArithmeticTrainingState, load_arithmetic_state, save_arithmetic_state


def test_arithmetic_training_state_full_router_root(tmp_path):
    state = ArithmeticTrainingState(seed=42)
    state.update({"stage": "single_op", "category": "current_supported_arithmetic"})
    manifest = save_arithmetic_state(state, tmp_path)
    loaded = load_arithmetic_state(tmp_path)
    assert manifest["persisted_state_support_level"] == "full_router_root"
    assert manifest["missing_for_full_state"] == []
    assert loaded.supported_seen == 1
