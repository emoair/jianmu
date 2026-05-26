from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.bounded_substrate_compiler_validation import run_bounded_substrate_compiler_validation


def test_bounded_substrate_compiler_validation_uses_cl(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "jianmu.self_learning.darwinforge.bounded_substrate_compiler_validation.run_turing_substrate_compiler_validation",
        lambda *a, **k: {"backend_type": "real_c_compiler", "compiler_name": "cl", "compile_worker_count": k.get("compile_worker_count", 16), "real_compiler_invocation_count": 1, "compiler_verified_correct_rate": 1.0, "boundary_compiler_misroute_count": 0},
    )
    result = run_bounded_substrate_compiler_validation("data", tmp_path, ["small"], 16)
    assert result["compiler_name"] == "cl"


def test_bounded_substrate_compiler_validation_uses_16_workers(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "jianmu.self_learning.darwinforge.bounded_substrate_compiler_validation.run_turing_substrate_compiler_validation",
        lambda *a, **k: {"backend_type": "real_c_compiler", "compiler_name": "cl", "compile_worker_count": 16, "real_compiler_invocation_count": 1, "compiler_verified_correct_rate": 1.0, "boundary_compiler_misroute_count": 0},
    )
    assert run_bounded_substrate_compiler_validation("data", tmp_path, ["small"], 16)["compile_worker_count"] == 16
