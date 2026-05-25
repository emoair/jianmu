from __future__ import annotations

import json
from pathlib import Path

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import CompilerBackend
from jianmu.self_learning.darwinforge.arithmetic_compiler_concurrency_readiness import (
    assess_compiler_concurrency_readiness,
)
from jianmu.self_learning.darwinforge.arithmetic_compiler_concurrency_scaling import (
    REQUIRED_WORKER_LEVELS,
    run_compiler_concurrency_scaling,
)


def test_concurrency_scaling_has_required_worker_levels() -> None:
    assert REQUIRED_WORKER_LEVELS == [4, 8, 16, 32, 64, 128, 256, 512]


def test_concurrency_scaling_uses_real_cl(tmp_path: Path, monkeypatch) -> None:
    dataset, fresh, longrun = _write_inputs(tmp_path)
    _patch_backend(monkeypatch)
    metrics = run_compiler_concurrency_scaling(tmp_path, fresh, longrun, dataset, tmp_path / "out", [4], supported_samples=4, boundary_samples=4)
    assert metrics["backend_type"] == "real_c_compiler"
    assert metrics["levels"][0]["compiler_name"] == "cl"


def test_concurrency_scaling_does_not_cache_results() -> None:
    source = Path("jianmu/self_learning/darwinforge/arithmetic_compiler_concurrency_scaling.py").read_text(encoding="utf-8")
    assert "result_cache" not in source
    assert "cached result" not in source.lower()


def test_concurrency_scaling_records_latency(tmp_path: Path, monkeypatch) -> None:
    dataset, fresh, longrun = _write_inputs(tmp_path)
    _patch_backend(monkeypatch)
    metrics = run_compiler_concurrency_scaling(tmp_path, fresh, longrun, dataset, tmp_path / "out", [4], supported_samples=4, boundary_samples=4)
    assert metrics["levels"][0]["p50_latency_ms"] >= 1.0
    assert metrics["levels"][0]["p99_latency_ms"] >= 1.0


def test_concurrency_scaling_records_spawn_errors() -> None:
    readiness = assess_compiler_concurrency_readiness({
        "backend_type": "real_c_compiler",
        "levels": [
            _level(4, 10.0, stable=True),
            _level(8, 12.0, stable=True),
            _level(16, 13.0, stable=True),
            _level(32, 14.0, stable=True),
            {**_level(64, 9.0, stable=False), "process_spawn_error_count": 2, "unstable_reason": "process_spawn_error_count"},
        ],
    })
    assert any(item["compile_worker_count"] == 64 for item in readiness["unstable_worker_levels"])


def test_concurrency_scaling_marks_unstable_level() -> None:
    readiness = assess_compiler_concurrency_readiness({
        "backend_type": "real_c_compiler",
        "levels": [_level(4, 10.0, stable=True), _level(8, 9.0, stable=False), _level(16, 8.0, stable=False), _level(32, 7.0, stable=False)],
    })
    assert readiness["recommended_claim_level"] in {"high_concurrency_unstable", "compiler_concurrency_scaling_profile_established"}


def test_concurrency_readiness_no_solved_claim() -> None:
    readiness = assess_compiler_concurrency_readiness({
        "backend_type": "real_c_compiler",
        "levels": [_level(4, 10.0), _level(8, 12.0), _level(16, 14.0), _level(32, 15.0), _level(128, 20.0)],
    })
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


def _level(workers: int, sps: float, stable: bool = True) -> dict:
    return {
        "compile_worker_count": workers,
        "completed": True,
        "stable": stable,
        "samples_per_second": sps,
        "real_compiler_invocation_count": 10,
        "compiler_verified_correct_rate": 1.0,
        "boundary_compiler_misroute_count": 0,
        "timeout_count": 0,
        "process_spawn_error_count": 0,
        "trace_write_error_count": 0,
    }


def _write_inputs(root: Path) -> tuple[Path, Path, Path]:
    dataset = root / "dataset" / "small" / "heldout"
    dataset.mkdir(parents=True)
    rows = []
    for idx in range(20):
        rows.append({
            "id": f"supported-{idx}",
            "split": "heldout",
            "stage": "single_op",
            "category": "current_supported_arithmetic",
            "input": "1+2",
            "canonical_expression": "1+2",
            "expected_output": "3",
        })
    for idx in range(10):
        rows.append({
            "id": f"boundary-{idx}",
            "split": "heldout",
            "stage": "boundary",
            "category": "hard_ood",
            "input": "tell me a joke",
            "canonical_expression": None,
        })
    (dataset / "heldout_000.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    fresh = root / "fresh"
    fresh.mkdir()
    (fresh / "fresh_compiler_trace.jsonl").write_text("", encoding="utf-8")
    longrun = root / "longrun"
    longrun.mkdir()
    (longrun / "compiler_longrun_trace_manifest.json").write_text(json.dumps({"shards": []}), encoding="utf-8")
    return root / "dataset", fresh, longrun


def _patch_backend(monkeypatch) -> None:
    import jianmu.self_learning.darwinforge.arithmetic_compiler_concurrency_scaling as scaling

    monkeypatch.setattr(scaling, "detect_arithmetic_backend", lambda prefer_python_subprocess=False, prefer_msvc=True: CompilerBackend(
        "real_c_compiler",
        "cl",
        "cl",
        compiler_environment="msvc_vcvars64",
    ))
    monkeypatch.setattr(scaling, "_execute_compiler", lambda expression, backend, timeout_seconds: {
        "backend_type": "real_c_compiler",
        "compiler_name": "cl",
        "compiler_invoked": True,
        "compile_returncode": 0,
        "compile_success": True,
        "runtime_returncode": 0,
        "runtime_success": True,
        "stdout_hash": _hash_text("3"),
        "stdout_value_if_safe": "3",
        "timeout": False,
        "unsafe_expression": False,
        "token_spacing_patch_applied": False,
        "latency_ms": 1.0,
        "notes": "",
    })


def _hash_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _source_text() -> str:
    return "\n".join(Path(path).read_text(encoding="utf-8") for path in [
        "jianmu/self_learning/darwinforge/arithmetic_compiler_concurrency_scaling.py",
        "jianmu/self_learning/darwinforge/arithmetic_compiler_concurrency_readiness.py",
    ])
