from jianmu.self_learning.darwinforge.full_router_state import FullRouterState


def test_full_router_state_to_dict_from_dict_roundtrip():
    state = FullRouterState.from_available_runtime(seed=42)
    restored = FullRouterState.from_dict(state.to_dict())
    assert restored.to_dict()["checksum"] == state.to_dict()["checksum"]
    assert restored.branch_layers
