from __future__ import annotations

from jianmu.self_learning.darwinforge.ironjudge_main20k_completion import write_main20k_completion_not_needed


def test_ironjudge_main20k_completion_only_if_needed(tmp_path) -> None:
    result = write_main20k_completion_not_needed(tmp_path, {"main_20k_effective_invocations": 27800})
    assert result["main20k_completion_rerun_executed"] is False
    assert result["new_invocation_count_v0_9_18_2"] == 0
