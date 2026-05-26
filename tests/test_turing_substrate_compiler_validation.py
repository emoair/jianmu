from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import CompilerBackend
from jianmu.self_learning.darwinforge.turing_substrate_compiler_validation import run_turing_substrate_compiler_validation, target_ir_to_c_source
from jianmu.self_learning.darwinforge.turing_substrate_generator import generate_scale


def test_turing_substrate_compiler_validation_uses_cl(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setitem(__import__("jianmu.self_learning.darwinforge.turing_substrate_generator", fromlist=["SCALE_TOTALS"]).SCALE_TOTALS, "small", 80)
    generate_scale("small", tmp_path / "data" / "small", seed=52, shard_size=50)
    monkeypatch.setattr(
        "jianmu.self_learning.darwinforge.turing_substrate_compiler_validation.detect_arithmetic_backend",
        lambda prefer_python_subprocess=False, prefer_msvc=True: CompilerBackend("real_c_compiler", "cl", "cl", "msvc_vcvars64"),
    )
    monkeypatch.setattr(
        "jianmu.self_learning.darwinforge.turing_substrate_compiler_validation._compile_and_run_source",
        lambda source, backend, timeout_seconds: {
            "compiler_invoked": True,
            "compile_returncode": 0,
            "compile_success": True,
            "runtime_invoked": True,
            "runtime_returncode": 0,
            "runtime_success": True,
            "stdout_hash": "x",
            "stdout_value_if_safe": source.split("/*EXPECTED:")[-1].split("*/")[0].strip() if "/*EXPECTED:" in source else "0",
            "timeout": False,
            "latency_ms": 1.0,
        },
    )
    monkeypatch.setattr(
        "jianmu.self_learning.darwinforge.turing_substrate_compiler_validation.target_ir_to_c_source",
        lambda ir: "/*EXPECTED:0*/",
    )
    metrics = run_turing_substrate_compiler_validation(tmp_path / "data", tmp_path / "records", ["small"], 16, 5, 5, 52, 1)
    assert metrics["backend_type"] == "real_c_compiler"
    assert metrics["compiler_name"] == "cl"


def test_turing_substrate_compiler_validation_uses_16_workers(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setitem(__import__("jianmu.self_learning.darwinforge.turing_substrate_generator", fromlist=["SCALE_TOTALS"]).SCALE_TOTALS, "small", 80)
    generate_scale("small", tmp_path / "data" / "small", seed=52, shard_size=50)
    monkeypatch.setattr(
        "jianmu.self_learning.darwinforge.turing_substrate_compiler_validation.detect_arithmetic_backend",
        lambda prefer_python_subprocess=False, prefer_msvc=True: CompilerBackend("unavailable", "", ""),
    )
    metrics = run_turing_substrate_compiler_validation(tmp_path / "data", tmp_path / "records", ["small"], 16, 5, 5, 52, 1)
    assert metrics["compile_worker_count"] == 16


def test_target_ir_to_c_source_contains_printf() -> None:
    source = target_ir_to_c_source({"op": "Program", "body": [{"op": "Print", "value": {"op": "Int", "value": 3}}]})
    assert "printf" in source


def test_turing_substrate_readiness_no_turing_complete_claim(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setitem(__import__("jianmu.self_learning.darwinforge.turing_substrate_generator", fromlist=["SCALE_TOTALS"]).SCALE_TOTALS, "small", 80)
    generate_scale("small", tmp_path / "data" / "small", seed=52, shard_size=50)
    monkeypatch.setattr(
        "jianmu.self_learning.darwinforge.turing_substrate_compiler_validation.detect_arithmetic_backend",
        lambda prefer_python_subprocess=False, prefer_msvc=True: CompilerBackend("unavailable", "", ""),
    )
    run_turing_substrate_compiler_validation(tmp_path / "data", tmp_path / "records", ["small"], 16, 5, 5, 52, 1)
    readiness = (tmp_path / "records" / "turing_substrate_readiness.json").read_text(encoding="utf-8").lower()
    assert "turing_complete" not in readiness


def test_no_expression_oracle_import() -> None:
    path = Path("jianmu/self_learning/darwinforge")
    assert "expression_oracle" not in "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in path.glob("turing_substrate_*.py"))


def test_no_external_api_calls() -> None:
    text = Path("jianmu/self_learning/darwinforge/turing_substrate_compiler_validation.py").read_text(encoding="utf-8")
    assert "openai" not in text.lower()
    assert "requests." not in text


def test_no_hardcoded_keyword_gate() -> None:
    text = Path("jianmu/self_learning/darwinforge/turing_substrate_generator.py").read_text(encoding="utf-8")
    assert "keyword gate" not in text.lower()


def test_real_promotion_disabled() -> None:
    from jianmu.self_learning.darwinforge.turing_substrate_curriculum_schedule import build_turing_substrate_curriculum_schedule

    assert all(not row["real_promotion_allowed"] for row in build_turing_substrate_curriculum_schedule()["stages"])
