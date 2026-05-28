from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.targeted_candidate_space_compiler_validation import run_targeted_compiler_validation


def test_compiler_validation_blocks_future_domain_compile(tmp_path) -> None:
    metrics = run_targeted_compiler_validation(tmp_path, [], [{"id": "f1", "category": "future_function_candidate"}], compile_worker_count=1)
    assert metrics["future_domain_compiled_count"] == 0
    assert metrics["real_compiler_invocation_count"] == 0


def test_targeted_compiler_validation_uses_real_cl_source() -> None:
    text = Path("jianmu/self_learning/darwinforge/targeted_candidate_space_compiler_validation.py").read_text(encoding="utf-8")
    assert "prefer_msvc=True" in text
    assert "validate_sample_with_temp_manager" in text

