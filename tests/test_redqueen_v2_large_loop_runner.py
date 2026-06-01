from __future__ import annotations

import json

from jianmu.self_learning.darwinforge.redqueen_v2_large_loop_runner import run_redqueen_v2_large_loop_probe


def test_redqueen_v2_large_loop_runner_checkpoint_partial(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "redqueen_v2_bandit_policy.json").write_text(json.dumps({"promoted_arms": ["bounded_for_loop", "wrong_top1_contrast_pairs"], "retired_arms": [], "epsilon_min": 0.05, "arm_selection_history": [{"selected_arm": "bounded_for_loop"}, {"selected_arm": "wrong_top1_contrast_pairs"}], "reward_trace": [{"reward": 0.2}, {"reward": 0.25}]}), encoding="utf-8")
    result = run_redqueen_v2_large_loop_probe(source, tmp_path / "records", tmp_path / "dataset", compiler_target=4, compile_worker_count=2)
    assert result["readiness"]["large_loop_completed"] is True
    assert result["materialization"]["partial_scales"]
