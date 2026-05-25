from __future__ import annotations

import json
from pathlib import Path

from jianmu.self_learning.darwinforge.arithmetic_compiler_failure_readiness import (
    assess_compiler_failure_readiness,
)
from jianmu.self_learning.darwinforge.arithmetic_compiler_failure_replay import (
    run_compiler_failure_taxonomy,
)
from jianmu.self_learning.darwinforge.arithmetic_compiler_failure_taxonomy import (
    classify_compiler_failure,
)


def test_compiler_failure_taxonomy_classifies_compile_error() -> None:
    row = {"sample_id_hash": "abc"}
    replay = {"compile_returncode": 2, "compile_stderr_tail": "error C2059: syntax error"}
    assert classify_compiler_failure(row, replay) == "compile_syntax_error"


def test_compiler_failure_taxonomy_classifies_runtime_error() -> None:
    row = {"sample_id_hash": "abc"}
    replay = {"compile_returncode": 0, "runtime_invoked": True, "runtime_returncode": 1}
    assert classify_compiler_failure(row, replay) == "runtime_error"


def test_compiler_failure_taxonomy_classifies_timeout() -> None:
    row = {"sample_id_hash": "abc"}
    replay = {"timeout": True, "runtime_invoked": True, "notes": "runtime_timeout"}
    assert classify_compiler_failure(row, replay) == "runtime_timeout"


def test_compiler_failure_replay_preserves_original_metrics(tmp_path: Path) -> None:
    source, dataset = _write_source_and_dataset(tmp_path)
    out = tmp_path / "out"
    summary = run_compiler_failure_taxonomy(source, out, dataset, rerun_failures=False)
    assert summary["original_result_preserved"] is True
    assert summary["original_compiler_invocation_count"] == 1
    assert (out / "patched_rerun_metrics.json").exists()


def test_compiler_failure_replay_does_not_skip_failures(tmp_path: Path) -> None:
    source, dataset = _write_source_and_dataset(tmp_path)
    out = tmp_path / "out"
    summary = run_compiler_failure_taxonomy(source, out, dataset, rerun_failures=False)
    assert summary["original_failure_count"] == 1
    assert summary["classified_failure_count"] == 1


def test_compiler_failure_readiness_no_solved_claim() -> None:
    readiness = assess_compiler_failure_readiness({
        "original_failure_count": 1,
        "classified_failure_count": 1,
        "unknown_failure_count": 0,
        "engineering_issue_dominant": True,
        "candidate_error_dominant": False,
        "patched_rerun_executed": True,
        "patched_delta_vs_original": 0.1,
        "patched_remaining_failure_count": 0,
        "original_result_preserved": True,
    })
    assert readiness["recommended_claim_level"] == "compiler_backed_signal_strengthened_after_patch"
    assert "solved" not in json.dumps(readiness).lower()


def test_no_expression_oracle_import() -> None:
    source = _source_text()
    assert "expression_oracle" not in source


def test_no_external_api_calls() -> None:
    source = _source_text().lower()
    assert "openai" not in source
    assert "requests." not in source


def test_no_hardcoded_keyword_gate() -> None:
    source = _source_text().lower()
    assert "keyword" not in source


def test_real_promotion_disabled() -> None:
    source = _source_text()
    assert "real_promotion" not in source


def _write_source_and_dataset(root: Path) -> tuple[Path, Path]:
    source = root / "records"
    source.mkdir()
    metrics = {
        "real_compiler_invocation_count": 1,
        "compiler_verified_correct_count": 0,
        "compiler_verified_failure_count": 1,
        "compiler_verified_correct_rate": 0.0,
        "compile_success_count": 0,
        "runtime_success_count": 0,
    }
    (source / "compiler_spot_metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
    (source / "compiler_audit_readiness.json").write_text("{}", encoding="utf-8")
    sample_id_hash = _hash_text("s1")
    expr_hash = _hash_text("1+2")
    trace = {
        "sample_id_hash": sample_id_hash,
        "split": "heldout",
        "stage": "precedence",
        "category": "current_supported_arithmetic",
        "candidate_expression_hash": expr_hash,
        "candidate_rank": 1,
        "compile_success": False,
        "runtime_success": False,
        "compiler_verified_correct": False,
        "expected_output_hash": _hash_text("3"),
    }
    (source / "compiler_spot_trace.jsonl").write_text(json.dumps(trace) + "\n", encoding="utf-8")

    dataset = root / "dataset" / "small" / "heldout"
    dataset.mkdir(parents=True)
    row = {
        "id": "s1",
        "split": "heldout",
        "stage": "precedence",
        "category": "current_supported_arithmetic",
        "input": "1+2",
        "canonical_expression": "1+2",
        "expected_output": "3",
    }
    (dataset / "heldout_000.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    return source, root / "dataset"


def _hash_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _source_text() -> str:
    paths = [
        "jianmu/self_learning/darwinforge/arithmetic_compiler_failure_taxonomy.py",
        "jianmu/self_learning/darwinforge/arithmetic_compiler_failure_replay.py",
        "jianmu/self_learning/darwinforge/arithmetic_compiler_failure_readiness.py",
    ]
    return "\n".join(Path(path).read_text(encoding="utf-8") for path in paths)
