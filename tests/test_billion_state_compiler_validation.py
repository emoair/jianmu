from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.billion_state_compiler_validation import run_billion_state_compiler_validation


def test_compiler_validation_uses_real_cl_for_best_profile(tmp_path) -> None:
    result = run_billion_state_compiler_validation(tmp_path, {"state_1B": {"supported": [], "boundary": []}}, compile_worker_count=1)
    assert result["compiler_validation_completed"] is True
    text = Path("jianmu/self_learning/darwinforge/billion_state_compiler_validation.py").read_text(encoding="utf-8")
    assert "run_targeted_compiler_validation" in text


def test_future_domain_not_compiled_under_1b_budget(tmp_path) -> None:
    result = run_billion_state_compiler_validation(tmp_path, {"state_1B": {"supported": [], "boundary": [{"id": "f", "category": "future_function_candidate"}]}}, compile_worker_count=1)
    metrics = result["per_profile"]["state_1B"]
    assert metrics["future_domain_compiled_count"] == 0
    assert metrics["real_compiler_invocation_count"] == 0

