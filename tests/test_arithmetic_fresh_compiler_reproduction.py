from __future__ import annotations

import json
from pathlib import Path

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import CompilerBackend
from jianmu.self_learning.darwinforge.arithmetic_fresh_compiler_readiness import (
    assess_fresh_compiler_readiness,
)
from jianmu.self_learning.darwinforge.arithmetic_fresh_compiler_reproduction import (
    apply_c_token_spacing_patch,
    run_fresh_compiler_reproduction,
)


def test_fresh_reproduction_uses_new_sample_ids(tmp_path: Path, monkeypatch) -> None:
    dataset, original = _write_dataset_and_original(tmp_path)
    _patch_backend(monkeypatch)
    out = tmp_path / "out"
    metrics = run_fresh_compiler_reproduction(tmp_path / "records", original, dataset, out, ["quick"], supported_samples=5, boundary_samples=5)
    assert metrics["fresh_supported_sample_count"] == 5
    assert metrics["original_overlap_count"] == 0
    assert metrics["fresh_ratio"] == 1.0


def test_fresh_reproduction_does_not_replay_original_600_only(tmp_path: Path, monkeypatch) -> None:
    dataset, original = _write_dataset_and_original(tmp_path)
    _patch_backend(monkeypatch)
    metrics = run_fresh_compiler_reproduction(tmp_path / "records", original, dataset, tmp_path / "out", ["quick"], supported_samples=5, boundary_samples=5)
    assert metrics["fresh_ratio"] >= 0.90
    assert metrics["recommended_claim_level"] == "fresh_compiler_backed_arithmetic_signal_reproduced"


def test_fresh_reproduction_invokes_real_compiler(tmp_path: Path, monkeypatch) -> None:
    dataset, original = _write_dataset_and_original(tmp_path)
    _patch_backend(monkeypatch)
    metrics = run_fresh_compiler_reproduction(tmp_path / "records", original, dataset, tmp_path / "out", ["quick"], supported_samples=3, boundary_samples=3)
    assert metrics["backend_type"] == "real_c_compiler"
    assert metrics["real_compiler_invocation_count"] == 3


def test_fresh_reproduction_preserves_token_spacing_patch() -> None:
    patched, applied = apply_c_token_spacing_patch("1--2 + 3+-4")
    assert applied is True
    assert "--" not in patched
    assert "+-" not in patched
    assert patched == "1- -2 + 3+ -4"


def test_fresh_reproduction_tracks_boundary_misroute(tmp_path: Path, monkeypatch) -> None:
    dataset, original = _write_dataset_and_original(tmp_path)
    _patch_backend(monkeypatch)
    metrics = run_fresh_compiler_reproduction(tmp_path / "records", original, dataset, tmp_path / "out", ["quick"], supported_samples=3, boundary_samples=5)
    assert metrics["boundary_compiler_misroute_count"] == 0
    assert metrics["unsupported_compiled_count"] == 0


def test_fresh_reproduction_readiness_no_solved_claim() -> None:
    readiness = assess_fresh_compiler_readiness({
        "modes_completed": ["quick"],
        "backend_type": "real_c_compiler",
        "compiler_name": "cl",
        "compiler_environment": "msvc_vcvars64",
        "fresh_ratio": 1.0,
        "real_compiler_invocation_count": 10,
        "compiler_verified_correct_rate": 1.0,
        "boundary_compiler_misroute_count": 0,
        "forbidden_field_access_count": 0,
        "backend_claim_safe": True,
        "token_spacing_patch_enabled": True,
    })
    assert readiness["recommended_claim_level"] == "fresh_compiler_backed_arithmetic_signal_reproduced"
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


def _write_dataset_and_original(root: Path) -> tuple[Path, Path]:
    dataset = root / "dataset" / "small" / "heldout"
    dataset.mkdir(parents=True)
    rows = []
    stages = ["precedence", "parentheses", "negative_numbers", "exact_division", "mixed_composition"]
    for idx in range(10):
        rows.append({
            "id": f"fresh-supported-{idx}",
            "split": "heldout",
            "stage": stages[idx % len(stages)],
            "category": "current_supported_arithmetic",
            "input": "1+2" if idx % 2 else "1--2",
            "canonical_expression": "1+2" if idx % 2 else "1--2",
            "expected_output": "3",
        })
    categories = [
        "unsupported_arithmetic_boundary",
        "true_false_accept_trap",
        "future_domain_candidate",
        "near_ood_arithmetic",
        "hard_ood",
    ]
    for idx, category in enumerate(categories):
        rows.append({
            "id": f"fresh-boundary-{idx}",
            "split": "heldout",
            "stage": "boundary_rejection",
            "category": category,
            "input": "1 / 0",
            "canonical_expression": None,
            "expected_output": None,
            "division_kind": "division_by_zero" if idx == 0 else "none",
        })
    (dataset / "heldout_000.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    original = root / "original"
    original.mkdir()
    (original / "compiler_spot_trace.jsonl").write_text(json.dumps({
        "sample_id_hash": _hash_text("old-supported"),
        "category": "current_supported_arithmetic",
    }) + "\n", encoding="utf-8")
    return root / "dataset", original


def _patch_backend(monkeypatch) -> None:
    import jianmu.self_learning.darwinforge.arithmetic_fresh_compiler_reproduction as fresh

    monkeypatch.setattr(fresh, "detect_arithmetic_backend", lambda prefer_python_subprocess=False, prefer_msvc=True: CompilerBackend(
        "real_c_compiler",
        "cl",
        "cl",
        compiler_environment="msvc_vcvars64",
    ))

    def fake_execute(expression, backend, timeout_seconds):
        patched, applied = fresh.apply_c_token_spacing_patch(expression)
        return {
            "backend_type": "real_c_compiler",
            "compiler_name": "cl",
            "compiler_environment": "msvc_vcvars64",
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
            "compile_stderr_tail": "",
            "runtime_stderr_tail": "",
            "token_spacing_patch_applied": applied or patched != expression,
            "latency_ms": 1.0,
            "notes": "",
        }

    monkeypatch.setattr(fresh, "_execute_compiler", fake_execute)


def _hash_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _source_text() -> str:
    paths = [
        "jianmu/self_learning/darwinforge/arithmetic_fresh_compiler_reproduction.py",
        "jianmu/self_learning/darwinforge/arithmetic_fresh_compiler_readiness.py",
    ]
    return "\n".join(Path(path).read_text(encoding="utf-8") for path in paths)
