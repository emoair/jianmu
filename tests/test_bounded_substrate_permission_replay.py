from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.bounded_substrate_permission_replay import _summarize_patched


def test_permission_replay_preserves_original_metrics() -> None:
    result = _summarize_patched([{"sample_id_hash": "a"}], [{"compiler_verified_correct": True, "compile_success": True, "runtime_success": True}], 1.0)
    assert result["original_result_preserved"] is True


def test_permission_replay_does_not_skip_failures() -> None:
    result = _summarize_patched([{"sample_id_hash": "a"}, {"sample_id_hash": "b"}], [{"compiler_verified_correct": True, "compile_success": True, "runtime_success": True}], 1.0)
    assert result["original_failure_count"] == 2
    assert result["patched_replay_sample_count"] == 1


def test_patched_replay_reports_separately() -> None:
    result = _summarize_patched([], [], 0.0)
    assert result["this_is_failure_replay_not_independent_full_rerun"] is True
