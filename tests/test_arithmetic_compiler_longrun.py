from __future__ import annotations

import json
from pathlib import Path

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import CompilerBackend
from jianmu.self_learning.darwinforge.arithmetic_compiler_longrun import run_compiler_longrun
from jianmu.self_learning.darwinforge.arithmetic_compiler_longrun_checkpoint import write_longrun_checkpoint
from jianmu.self_learning.darwinforge.arithmetic_compiler_longrun_readiness import assess_compiler_longrun_readiness


def test_compiler_longrun_uses_real_cl(tmp_path: Path, monkeypatch) -> None:
    dataset, fresh = _write_dataset_and_fresh(tmp_path)
    _patch_backend(monkeypatch)
    metrics = run_compiler_longrun(tmp_path / "records", fresh, dataset, tmp_path / "out", ["quick"], supported_samples=5, boundary_samples=5)
    assert metrics["backend_type"] == "real_c_compiler"
    assert metrics["compiler_name"] == "cl"
    assert metrics["real_compiler_invocation_count"] == 5


def test_compiler_longrun_rejects_non_compiler_backend_claim() -> None:
    readiness = assess_compiler_longrun_readiness({
        "backend_type": "python_subprocess_executor",
        "real_compiler_invocation_count": 50000,
        "compiler_verified_correct_rate": 1.0,
        "fresh_longrun_ratio": 1.0,
        "boundary_compiler_misroute_count": 0,
        "forbidden_field_access_count": 0,
        "backend_claim_safe": True,
    })
    assert readiness["recommended_claim_level"] == "compiler_unavailable"


def test_compiler_longrun_writes_checkpoints(tmp_path: Path) -> None:
    path = tmp_path / "checkpoints.jsonl"
    write_longrun_checkpoint(path, {"mode": "quick", "supported_sample_count": 1})
    assert path.exists()
    assert json.loads(path.read_text(encoding="utf-8"))["mode"] == "quick"


def test_compiler_longrun_marks_partial_correctly(tmp_path: Path, monkeypatch) -> None:
    dataset, fresh = _write_dataset_and_fresh(tmp_path)
    _patch_backend(monkeypatch)
    metrics = run_compiler_longrun(
        tmp_path / "records",
        fresh,
        dataset,
        tmp_path / "out",
        ["longrun"],
        supported_samples=10,
        boundary_samples=5,
        max_runtime_hours=0.000001,
    )
    assert "longrun" not in metrics["modes_completed"]
    assert metrics["modes_partial_skipped"]


def test_compiler_longrun_preserves_boundary_guard(tmp_path: Path, monkeypatch) -> None:
    dataset, fresh = _write_dataset_and_fresh(tmp_path)
    _patch_backend(monkeypatch)
    metrics = run_compiler_longrun(tmp_path / "records", fresh, dataset, tmp_path / "out", ["quick"], supported_samples=5, boundary_samples=5)
    assert metrics["boundary_compiler_misroute_count"] == 0
    assert metrics["unsupported_compiled_count"] == 0


def test_compiler_longrun_no_result_cache_cheating() -> None:
    source = Path("jianmu/self_learning/darwinforge/arithmetic_compiler_longrun.py").read_text(encoding="utf-8")
    assert "cached result" not in source.lower()
    assert "result_cache" not in source


def test_compiler_longrun_readiness_no_solved_claim() -> None:
    readiness = assess_compiler_longrun_readiness({
        "backend_type": "real_c_compiler",
        "real_compiler_invocation_count": 20000,
        "compiler_verified_correct_rate": 1.0,
        "fresh_longrun_ratio": 1.0,
        "boundary_compiler_misroute_count": 0,
        "forbidden_field_access_count": 0,
        "backend_claim_safe": True,
        "modes_partial_skipped": [],
    })
    assert readiness["recommended_claim_level"] == "compiler_backed_arithmetic_longrun_signal"
    assert "solved" not in json.dumps(readiness).lower()


def test_no_expression_oracle_import() -> None:
    assert "expression_oracle" not in _source_text()


def test_no_external_api_calls() -> None:
    source = _source_text().lower()
    assert "openai" not in source
    assert "requests." not in source


def test_no_hardcoded_keyword_gate() -> None:
    assert "keyword" not in _source_text().lower()


def test_real_promotion_disabled() -> None:
    assert "real_promotion" not in _source_text()


def _write_dataset_and_fresh(root: Path) -> tuple[Path, Path]:
    dataset = root / "dataset" / "small" / "heldout"
    dataset.mkdir(parents=True)
    stages = ["single_op", "two_op_no_parentheses", "precedence", "parentheses", "negative_numbers", "exact_division", "mixed_composition"]
    rows = []
    for idx in range(30):
        rows.append({
            "id": f"supported-{idx}",
            "split": "heldout",
            "stage": stages[idx % len(stages)],
            "category": "current_supported_arithmetic",
            "input": "1+2",
            "canonical_expression": "1+2",
            "expected_output": "3",
        })
    for idx, category in enumerate(["unsupported_arithmetic_boundary", "true_false_accept_trap", "future_domain_candidate", "near_ood_arithmetic", "hard_ood"]):
        rows.append({
            "id": f"boundary-{idx}",
            "split": "heldout",
            "stage": "boundary",
            "category": category,
            "input": "1/0",
            "canonical_expression": None,
            "division_kind": "division_by_zero" if idx == 0 else "none",
        })
    (dataset / "heldout_000.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    fresh = root / "fresh"
    fresh.mkdir()
    (fresh / "fresh_compiler_trace.jsonl").write_text("", encoding="utf-8")
    return root / "dataset", fresh


def _patch_backend(monkeypatch) -> None:
    import jianmu.self_learning.darwinforge.arithmetic_compiler_longrun as longrun

    monkeypatch.setattr(longrun, "detect_arithmetic_backend", lambda prefer_python_subprocess=False, prefer_msvc=True: CompilerBackend(
        "real_c_compiler",
        "cl",
        "cl",
        compiler_environment="msvc_vcvars64",
    ))
    monkeypatch.setattr(longrun, "_execute_compiler", lambda expression, backend, timeout_seconds: {
        "backend_type": "real_c_compiler",
        "compiler_name": "cl",
        "compiler_invoked": True,
        "compile_returncode": 0,
        "compile_success": True,
        "runtime_invoked": True,
        "runtime_returncode": 0,
        "runtime_success": True,
        "stdout_hash": _hash_text("3"),
        "stdout_value_if_safe": "3",
        "timeout": False,
        "unsafe_expression": False,
        "token_spacing_patch_applied": "--" in expression,
        "compile_stderr_tail": "",
        "runtime_stderr_tail": "",
        "latency_ms": 1.0,
        "notes": "",
    })


def _hash_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _source_text() -> str:
    paths = [
        "jianmu/self_learning/darwinforge/arithmetic_compiler_longrun.py",
        "jianmu/self_learning/darwinforge/arithmetic_compiler_longrun_readiness.py",
        "jianmu/self_learning/darwinforge/arithmetic_compiler_longrun_failure_summary.py",
    ]
    return "\n".join(Path(path).read_text(encoding="utf-8") for path in paths)
