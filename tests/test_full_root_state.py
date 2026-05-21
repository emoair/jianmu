from jianmu.self_learning.darwinforge.full_root_state import FullRootState


def test_full_root_state_to_dict_from_dict_roundtrip():
    state = FullRootState.from_available_runtime(seed=42)
    restored = FullRootState.from_dict(state.to_dict())
    assert restored.to_dict()["checksum"] == state.to_dict()["checksum"]
    assert restored.root_status["active"] == 0
