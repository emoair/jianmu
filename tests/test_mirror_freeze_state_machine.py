import pytest

from jianmu.self_learning.darwinforge.mirror_freeze_state_machine import apply_lane_update, build_mirror_state, run_mirror_freeze_state_machine
from jianmu.self_learning.darwinforge.mirror_landing_schema import INVALID_BOTH_ACTIVE, LANE_A_ACTIVE_LANE_B_FROZEN


def test_mirror_freeze_state_machine_rejects_simultaneous_active() -> None:
    with pytest.raises(ValueError):
        build_mirror_state(0, INVALID_BOTH_ACTIVE)


def test_mirror_freeze_state_machine_rejects_frozen_mutation(tmp_path) -> None:
    state = build_mirror_state(0, LANE_A_ACTIVE_LANE_B_FROZEN)
    assert apply_lane_update(state, "lane_b")["allowed"] is False
    result = run_mirror_freeze_state_machine(tmp_path)
    assert result["frozen_mutation_rejected"] is True

