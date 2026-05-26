from __future__ import annotations

from jianmu.self_learning.darwinforge.bounded_substrate_worker_scaling import REQUIRED_WORKER_LEVELS


def test_bounded_substrate_worker_scaling_levels_are_bounded() -> None:
    assert REQUIRED_WORKER_LEVELS == [8, 16, 32, 64]
