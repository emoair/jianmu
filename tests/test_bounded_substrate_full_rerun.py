from __future__ import annotations

from jianmu.self_learning.darwinforge.bounded_substrate_full_rerun import FULL_LIMITS


def test_bounded_substrate_full_rerun_large_limits() -> None:
    assert FULL_LIMITS["full-probe"]["scale"] == "large"
    assert FULL_LIMITS["full-probe"]["compiler"] == 10000
