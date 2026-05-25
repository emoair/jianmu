from __future__ import annotations

import json
from pathlib import Path

from jianmu.self_learning.darwinforge.arithmetic_compiler_audit_readiness import assess_compiler_audit_readiness
from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import (
    CompilerBackend,
    detect_arithmetic_backend,
    execute_with_backend,
    generate_safe_c_program,
    is_safe_c_arithmetic_expression,
)
from jianmu.self_learning.darwinforge.arithmetic_compiler_spot_audit import run_real_compiler_arithmetic_spot_audit


def _supported(idx: int, split: str, stage: str, expression: str, expected: str) -> dict:
    return {
        "id": f"{split}-{stage}-{idx}",
        "split": split,
        "stage": stage,
        "category": "current_supported_arithmetic",
        "input": expression,
        "canonical_expression": expression,
        "target_ir": {"op": "int", "value": int(expected)},
        "expected_output": expected,
    }


def _boundary(idx: int, split: str, category: str, text: str) -> dict:
    return {
        "id": f"{split}-{category}-{idx}",
        "split": split,
        "stage": "boundary_rejection",
        "category": category,
        "input": text,
        "canonical_expression": None,
        "target_ir": None,
        "expected_output": None,
    }


def _write_dataset(root: Path) -> None:
    rows = [
        _supported(1, "heldout", "precedence", "1+2*3", "7"),
        _supported(2, "heldout", "parentheses", "(1+2)*3", "9"),
        _supported(3, "heldout", "negative_numbers", "-3+5", "2"),
        _supported(4, "heldout", "exact_division", "8/2", "4"),
        _supported(5, "heldout", "mixed_composition", "(8/2)+3*2", "10"),
        _boundary(1, "heldout", "unsupported_arithmetic_boundary", "1 / 0"),
        _boundary(2, "heldout", "true_false_accept_trap", "3 + apple"),
        _boundary(3, "heldout", "future_domain_candidate", "3.14 * 2"),
        _boundary(4, "heldout", "near_ood_arithmetic", "7 / 2"),
        _boundary(5, "heldout", "hard_ood", "tell me a joke"),
    ]
    split_dir = root / "small" / "heldout"
    split_dir.mkdir(parents=True, exist_ok=True)
    (split_dir / "heldout_000.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_compiler_backend_detects_available_compiler() -> None:
    backend = detect_arithmetic_backend()
    assert backend.backend_type in {"real_c_compiler", "python_subprocess_executor", "unavailable"}
    if backend.backend_type == "real_c_compiler":
        assert backend.compiler_name in {"gcc", "clang", "cl"}


def test_compiler_backend_marks_unavailable_honestly(monkeypatch) -> None:
    import jianmu.self_learning.darwinforge.arithmetic_compiler_backend as backend_module

    monkeypatch.setattr(backend_module, "detect_supported_c_compiler", lambda: (None, ""))
    monkeypatch.setattr(backend_module, "detect_msvc_and_path_compilers", lambda: {
        "path_cl_found": False,
        "path_gcc_found": False,
        "path_clang_found": False,
        "vswhere_found": False,
        "vcvars64_found": False,
        "vcvars64_path": "",
        "cl_bv_test_passed": False,
        "cl_version_text_tail": "",
        "detection_conclusion": "no_c_compiler_detected",
    })
    backend = backend_module.detect_arithmetic_backend(prefer_python_subprocess=False)
    assert backend.backend_type == "unavailable"
    assert not backend.compiler_available


def test_compiler_backend_generates_safe_c_program() -> None:
    program = generate_safe_c_program("(3 + 5) * 2")
    assert "#include <stdio.h>" in program
    assert "printf" in program
    assert "(3 + 5) * 2" in program


def test_compiler_backend_rejects_unsafe_expression() -> None:
    assert not is_safe_c_arithmetic_expression("3 + system(1)")
    result = execute_with_backend("3 + system(1)", CompilerBackend("unavailable", "", ""))
    assert result["unsafe_expression"] is True
    assert result["compiler_invoked"] is False


def test_compiler_spot_audit_invokes_subprocess_when_available(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    out = tmp_path / "records"
    records = tmp_path / "v0_9_3_2"
    records.mkdir()
    (records / "candidate_trace_manifest.json").write_text("{}", encoding="utf-8")
    _write_dataset(dataset)
    metrics = run_real_compiler_arithmetic_spot_audit(records, dataset, out, ["quick"], supported_samples=5, boundary_samples=5)
    assert metrics["backend_type"] in {"real_c_compiler", "python_subprocess_executor", "unavailable"}
    if metrics["backend_type"] == "real_c_compiler":
        assert metrics["real_compiler_invocation_count"] > 0
        assert metrics["compiler_verified_correct_rate"] is not None
    else:
        assert metrics["recommended_claim_level"] != "compiler_backed_arithmetic_spot_signal"


def test_compiler_spot_audit_does_not_call_internal_evaluator_as_compiler(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    out = tmp_path / "records"
    records = tmp_path / "v0_9_3_2"
    records.mkdir()
    (records / "candidate_trace_manifest.json").write_text("{}", encoding="utf-8")
    _write_dataset(dataset)
    metrics = run_real_compiler_arithmetic_spot_audit(records, dataset, out, ["quick"], supported_samples=5, boundary_samples=5)
    assert metrics["internal_evaluator_call_count"] == 0
    assert metrics["backend_claim_safe"] is True


def test_compiler_audit_readiness_no_solved_claim() -> None:
    readiness = assess_compiler_audit_readiness({
        "audit_completed": True,
        "backend_type": "python_subprocess_executor",
        "real_compiler_invocation_count": 0,
        "compiler_verified_correct_rate": None,
        "boundary_compiler_misroute_count": 0,
        "forbidden_field_access_count": 0,
        "backend_claim_safe": True,
    })
    assert readiness["recommended_claim_level"] == "execution_backed_but_not_compiler"
    assert "solved" not in json.dumps(readiness).lower()


def test_no_expression_oracle_import() -> None:
    source = "\n".join(Path(path).read_text(encoding="utf-8") for path in [
        "jianmu/self_learning/darwinforge/arithmetic_compiler_backend.py",
        "jianmu/self_learning/darwinforge/arithmetic_compiler_spot_audit.py",
    ])
    assert "expression_oracle" not in source


def test_no_external_api_calls() -> None:
    source = "\n".join(Path(path).read_text(encoding="utf-8") for path in [
        "jianmu/self_learning/darwinforge/arithmetic_compiler_backend.py",
        "jianmu/self_learning/darwinforge/arithmetic_compiler_spot_audit.py",
    ])
    assert "openai" not in source.lower()
    assert "requests." not in source


def test_no_hardcoded_keyword_gate() -> None:
    source = Path("jianmu/self_learning/darwinforge/arithmetic_compiler_spot_audit.py").read_text(encoding="utf-8")
    assert "keyword" not in source.lower()


def test_real_promotion_disabled() -> None:
    source = Path("jianmu/self_learning/darwinforge/arithmetic_compiler_spot_audit.py").read_text(encoding="utf-8")
    assert "real_promotion" not in source
