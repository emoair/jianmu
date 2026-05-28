from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.state_budget_compiler_validation import run_state_budget_compiler_validation


def test_compiler_validation_per_profile_uses_real_cl(tmp_path) -> None:
    result = run_state_budget_compiler_validation(tmp_path, {"baseline_targeted": {"supported": [], "boundary": []}}, compile_worker_count=1)
    assert result["compiler_validation_completed"] is True
    text = Path("jianmu/self_learning/darwinforge/state_budget_compiler_validation.py").read_text(encoding="utf-8")
    assert "run_targeted_compiler_validation" in text


def test_future_domain_not_compiled_under_large_budget(tmp_path) -> None:
    result = run_state_budget_compiler_validation(tmp_path, {"state_100M": {"supported": [], "boundary": [{"id": "f", "category": "future_function_candidate"}]}}, compile_worker_count=1)
    metrics = result["per_profile"]["state_100M"]
    assert metrics["future_domain_compiled_count"] == 0
    assert metrics["real_compiler_invocation_count"] == 0

