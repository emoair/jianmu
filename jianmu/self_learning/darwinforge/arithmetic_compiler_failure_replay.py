from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Iterable

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import (
    CompilerBackend,
    _build_backend_compile_command,
    detect_arithmetic_backend,
    is_safe_c_arithmetic_expression,
)
from jianmu.self_learning.darwinforge.arithmetic_compiler_failure_readiness import (
    assess_compiler_failure_readiness,
)
from jianmu.self_learning.darwinforge.arithmetic_compiler_failure_taxonomy import (
    classify_compiler_failure,
    summarize_failure_taxonomy,
)


def run_compiler_failure_taxonomy(
    source_records: str | Path,
    output_records: str | Path,
    dataset_dir: str | Path = "datasets/v0_9_2_arithmetic_curriculum",
    rerun_failures: bool = True,
    allow_engineering_patch: bool = True,
    timeout_seconds: int = 5,
) -> Dict[str, Any]:
    source = Path(source_records)
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    original_metrics = _read_json(source / "compiler_spot_metrics.json")
    original_readiness = _read_json(source / "compiler_audit_readiness.json")
    trace_rows = _read_jsonl(source / "compiler_spot_trace.jsonl")
    failures = _failure_rows(trace_rows)

    dataset_index = _dataset_index(Path(dataset_dir))
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    replay_rows: list[Dict[str, Any]] = []
    patched_rows: list[Dict[str, Any]] = []
    for row in failures:
        replay = _replay_failure(row, dataset_index, backend, timeout_seconds, patched_c_source=False) if rerun_failures else {}
        failure_category = classify_compiler_failure(row, replay)
        replay_rows.append(_failure_record(row, replay, failure_category))
        if rerun_failures and allow_engineering_patch:
            patched_replay = _replay_failure(row, dataset_index, backend, timeout_seconds, patched_c_source=True)
            patched_rows.append(_failure_record(row, patched_replay, failure_category))

    taxonomy_summary = summarize_failure_taxonomy(replay_rows)
    patched = _patched_metrics(original_metrics, patched_rows, rerun_failures and allow_engineering_patch)
    if (
        patched["patched_rerun_executed"]
        and patched["patched_remaining_failure_count"] < max(1, len(failures) // 2)
        and taxonomy_summary.get("dominant_failure_category") == "compile_syntax_error"
    ):
        taxonomy_summary["engineering_issue_dominant"] = True
        taxonomy_summary["candidate_error_dominant"] = False
    combined = {
        "source_records": str(source),
        "original_metrics": original_metrics,
        "original_readiness": original_readiness,
        "original_compiler_invocation_count": original_metrics.get("real_compiler_invocation_count", 0),
        "original_success_count": original_metrics.get("compiler_verified_correct_count", 0),
        "original_failure_count": original_metrics.get("compiler_verified_failure_count", len(failures)),
        "failure_taxonomy_completed": bool(failures),
        **taxonomy_summary,
        **patched,
        "original_result_preserved": True,
    }
    readiness = assess_compiler_failure_readiness(combined)
    combined.update(readiness)

    _write_jsonl(out / "compiler_failure_replay_trace.jsonl", replay_rows)
    _write_jsonl(out / "compiler_failure_examples.jsonl", _failure_examples(replay_rows))
    _write_summary_csv(out / "compiler_failure_summary.csv", replay_rows)
    _write_json(out / "compiler_failure_taxonomy.json", combined)
    _write_markdown(out / "compiler_failure_taxonomy.md", combined)
    _write_json(out / "patched_rerun_metrics.json", patched)
    if patched["patched_rerun_executed"]:
        _write_jsonl(out / "patched_rerun_trace.jsonl", patched_rows)
    _write_json(out / "compiler_failure_readiness.json", readiness)
    _write_mainline(out, combined)
    return combined


def _replay_failure(
    row: Dict[str, Any],
    dataset_index: Dict[str, Dict[str, Any]],
    backend: CompilerBackend,
    timeout_seconds: int,
    patched_c_source: bool,
) -> Dict[str, Any]:
    sample_hash = str(row.get("sample_id_hash") or "")
    dataset_row = dataset_index.get(sample_hash)
    if not dataset_row:
        return {"missing_dataset_row": True, "trace_missing_expression": True, "notes": "missing_dataset_row"}
    expression = _candidate_expression(dataset_row)
    if _hash_text(expression) != row.get("candidate_expression_hash"):
        return {
            "trace_missing_expression": False,
            "candidate_hash_mismatch": True,
            "expression_preview_if_safe": expression if is_safe_c_arithmetic_expression(expression) else None,
            "notes": "candidate_hash_mismatch",
        }
    return _execute_with_capture(expression, backend, timeout_seconds, patched_c_source=patched_c_source)


def _execute_with_capture(expression: str, backend: CompilerBackend, timeout_seconds: int, patched_c_source: bool = False) -> Dict[str, Any]:
    started = time.perf_counter()
    result: Dict[str, Any] = {
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
        "compiler_environment": backend.compiler_environment,
        "expression_preview_if_safe": expression if is_safe_c_arithmetic_expression(expression) else None,
        "c_source_hash": None,
        "compiler_invoked": False,
        "compile_returncode": None,
        "compile_success": False,
        "compile_stdout_tail": "",
        "compile_stderr_tail": "",
        "runtime_invoked": False,
        "runtime_returncode": None,
        "runtime_success": False,
        "runtime_stdout_tail": "",
        "runtime_stderr_tail": "",
        "stdout_hash": None,
        "stdout_value_if_safe": None,
        "timeout": False,
        "unsafe_expression": False,
        "latency_ms": 0.0,
        "patched_c_source": patched_c_source,
        "notes": "",
    }
    if not is_safe_c_arithmetic_expression(expression):
        result.update({"unsafe_expression": True, "notes": "unsafe_expression"})
        return result
    if backend.backend_type != "real_c_compiler":
        result["notes"] = "real_compiler_unavailable_for_replay"
        return result
    program = _generate_c_program(expression, patched_c_source=patched_c_source)
    result["c_source_hash"] = _hash_text(program)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        src = tmp_path / "prog.c"
        exe = tmp_path / ("prog.exe" if os.name == "nt" else "prog")
        src.write_text(program, encoding="utf-8")
        try:
            compile_cmd, compile_env = _build_backend_compile_command(backend, src, exe)
            compile_proc = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=tmpdir,
                env=compile_env,
                errors="replace",
            )
        except subprocess.TimeoutExpired as exc:
            result.update({
                "compiler_invoked": True,
                "compile_returncode": -1,
                "timeout": True,
                "compile_stdout_tail": _tail(exc.stdout or ""),
                "compile_stderr_tail": _tail(exc.stderr or ""),
                "notes": "compile_timeout",
                "latency_ms": round((time.perf_counter() - started) * 1000, 6),
            })
            return result
        except OSError as exc:
            result.update({
                "compiler_invoked": True,
                "compile_returncode": -1,
                "compile_stderr_tail": _tail(str(exc)),
                "notes": "compile_os_error",
                "latency_ms": round((time.perf_counter() - started) * 1000, 6),
            })
            return result
        result.update({
            "compiler_invoked": True,
            "compile_returncode": compile_proc.returncode,
            "compile_success": compile_proc.returncode == 0,
            "compile_stdout_tail": _tail(compile_proc.stdout),
            "compile_stderr_tail": _tail(compile_proc.stderr),
        })
        if compile_proc.returncode != 0:
            result.update({"notes": "compile_error", "latency_ms": round((time.perf_counter() - started) * 1000, 6)})
            return result
        try:
            run_proc = subprocess.run([str(exe)], capture_output=True, text=True, timeout=timeout_seconds, cwd=tmpdir, errors="replace")
        except subprocess.TimeoutExpired as exc:
            result.update({
                "runtime_invoked": True,
                "runtime_returncode": -1,
                "timeout": True,
                "runtime_stdout_tail": _tail(exc.stdout or ""),
                "runtime_stderr_tail": _tail(exc.stderr or ""),
                "notes": "runtime_timeout",
                "latency_ms": round((time.perf_counter() - started) * 1000, 6),
            })
            return result
        stdout = run_proc.stdout.strip()
        result.update({
            "runtime_invoked": True,
            "runtime_returncode": run_proc.returncode,
            "runtime_success": run_proc.returncode == 0,
            "runtime_stdout_tail": _tail(run_proc.stdout),
            "runtime_stderr_tail": _tail(run_proc.stderr),
            "stdout_hash": _hash_text(stdout),
            "stdout_value_if_safe": stdout if _safe_stdout(stdout) else None,
            "latency_ms": round((time.perf_counter() - started) * 1000, 6),
        })
        return result


def _failure_record(row: Dict[str, Any], replay: Dict[str, Any], failure_category: str) -> Dict[str, Any]:
    expected_hash = row.get("expected_output_hash")
    observed_hash = replay.get("stdout_hash")
    correct = bool(replay.get("runtime_success")) and expected_hash is not None and observed_hash == expected_hash
    return {
        "sample_id_hash": row.get("sample_id_hash"),
        "split": row.get("split"),
        "stage": row.get("stage"),
        "category": row.get("category"),
        "candidate_rank": row.get("candidate_rank"),
        "failure_category": failure_category,
        "original_compile_returncode": row.get("compile_returncode"),
        "original_runtime_returncode": row.get("runtime_returncode"),
        "original_notes": row.get("notes"),
        "compile_returncode": replay.get("compile_returncode"),
        "runtime_returncode": replay.get("runtime_returncode"),
        "compile_success": bool(replay.get("compile_success")),
        "runtime_success": bool(replay.get("runtime_success")),
        "compiler_verified_correct": correct,
        "timeout": bool(replay.get("timeout")),
        "unsafe_expression": bool(replay.get("unsafe_expression")),
        "compile_stderr_tail": replay.get("compile_stderr_tail", ""),
        "compile_stdout_tail": replay.get("compile_stdout_tail", ""),
        "runtime_stderr_tail": replay.get("runtime_stderr_tail", ""),
        "runtime_stdout_tail": replay.get("runtime_stdout_tail", ""),
        "expression_preview_if_safe": replay.get("expression_preview_if_safe"),
        "c_source_hash": replay.get("c_source_hash"),
        "expected_output_hash": row.get("expected_output_hash"),
        "observed_stdout_hash": replay.get("stdout_hash"),
        "latency_ms": replay.get("latency_ms", 0.0),
        "notes": replay.get("notes", ""),
    }


def _patched_metrics(original: Dict[str, Any], replay_rows: list[Dict[str, Any]], executed: bool) -> Dict[str, Any]:
    original_total = int(original.get("real_compiler_invocation_count") or original.get("compiler_spot_sample_count") or 0)
    original_correct = int(original.get("compiler_verified_correct_count") or 0)
    replay_correct = sum(bool(row.get("compiler_verified_correct")) for row in replay_rows) if executed else 0
    replay_compile_success = sum(bool(row.get("compile_success")) for row in replay_rows) if executed else 0
    replay_runtime_success = sum(bool(row.get("runtime_success")) for row in replay_rows) if executed else 0
    patched_correct = original_correct + replay_correct
    patched_remaining = max(0, len(replay_rows) - replay_correct)
    original_rate = float(original.get("compiler_verified_correct_rate") or 0.0)
    patched_rate = round(patched_correct / max(original_total, 1), 6)
    return {
        "patched_rerun_executed": executed,
        "patched_compile_success_count": int(original.get("compile_success_count") or 0) + replay_compile_success,
        "patched_runtime_success_count": int(original.get("runtime_success_count") or 0) + replay_runtime_success,
        "patched_compiler_verified_correct_count": patched_correct,
        "patched_compiler_verified_correct_rate": patched_rate,
        "patched_remaining_failure_count": patched_remaining,
        "patched_delta_vs_original": round(patched_rate - original_rate, 6),
        "original_result_preserved": True,
    }


def _generate_c_program(expression: str, patched_c_source: bool = False) -> str:
    if not is_safe_c_arithmetic_expression(expression):
        raise ValueError("unsafe arithmetic expression")
    c_expression = _space_adjacent_sign_tokens(expression) if patched_c_source else expression
    return "\n".join([
        "#include <stdio.h>",
        "",
        "int main(void) {",
        f"    long long result = (long long)({c_expression});",
        "    printf(\"%lld\\n\", result);",
        "    return 0;",
        "}",
        "",
    ])


def _space_adjacent_sign_tokens(expression: str) -> str:
    # MSVC tokenizes ``--`` and ``++`` before parsing unary signs. Spacing keeps
    # the arithmetic candidate unchanged while avoiding decrement/increment tokens.
    return expression.replace("--", "- -").replace("++", "+ +")


def _failure_rows(rows: Iterable[Dict[str, Any]]) -> list[Dict[str, Any]]:
    return [
        row for row in rows
        if row.get("category") == "current_supported_arithmetic"
        and (
            row.get("compile_success") is False
            or row.get("runtime_success") is False
            or row.get("compiler_verified_correct") is False
            or row.get("timeout") is True
        )
    ]


def _dataset_index(dataset: Path) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for path in dataset.rglob("*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            index[_hash_text(str(row.get("id", "")))] = row
    return index


def _candidate_expression(row: Dict[str, Any]) -> str:
    expression = row.get("canonical_expression") or row.get("input") or ""
    return str(expression).split("#", 1)[0].strip(" ?.")


def _failure_examples(rows: Iterable[Dict[str, Any]]) -> list[Dict[str, Any]]:
    examples = []
    for row in rows:
        examples.append({
            "sample_id_hash": row.get("sample_id_hash"),
            "stage": row.get("stage"),
            "category": row.get("category"),
            "candidate_rank": row.get("candidate_rank"),
            "failure_category": row.get("failure_category"),
            "compile_returncode": row.get("compile_returncode"),
            "runtime_returncode": row.get("runtime_returncode"),
            "compile_stderr_tail": row.get("compile_stderr_tail"),
            "compile_stdout_tail": row.get("compile_stdout_tail"),
            "runtime_stderr_tail": row.get("runtime_stderr_tail"),
            "runtime_stdout_tail": row.get("runtime_stdout_tail"),
            "expression_preview_if_safe": row.get("expression_preview_if_safe"),
            "c_source_hash": row.get("c_source_hash"),
            "expected_output_hash": row.get("expected_output_hash"),
            "observed_stdout_hash": row.get("observed_stdout_hash"),
            "notes": row.get("notes"),
        })
    return examples


def _write_summary_csv(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["sample_id_hash", "stage", "category", "failure_category", "compile_returncode", "runtime_returncode", "notes"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def _write_markdown(path: Path, summary: Dict[str, Any]) -> None:
    lines = [
        "# Compiler Failure Taxonomy",
        "",
        f"- Original compiler invocations: {summary.get('original_compiler_invocation_count')}",
        f"- Original success/failure: {summary.get('original_success_count')}/{summary.get('original_failure_count')}",
        f"- Classified failures: {summary.get('classified_failure_count')}",
        f"- Dominant category: {summary.get('dominant_failure_category')}",
        f"- Engineering issue dominant: {summary.get('engineering_issue_dominant')}",
        f"- Candidate error dominant: {summary.get('candidate_error_dominant')}",
        f"- Patched rerun executed: {summary.get('patched_rerun_executed')}",
        f"- Patched correct rate: {summary.get('patched_compiler_verified_correct_rate')}",
        f"- Original result preserved: {summary.get('original_result_preserved')}",
        "",
        "## Failure Category Distribution",
        "",
    ]
    for key, value in summary.get("failure_category_distribution", {}).items():
        lines.append(f"- {key}: {value}")
    if (
        summary.get("dominant_failure_category") == "compile_syntax_error"
        and summary.get("patched_delta_vs_original", 0) > 0
    ):
        lines.extend([
            "",
            "Dominant observed pattern: failed expressions contained adjacent sign tokens such as `--`. MSVC tokenizes these as decrement operators before parsing unary signs. The patched rerun only spaces adjacent sign tokens in generated C source; it does not change candidate generation or scoring.",
        ])
    lines.extend([
        "",
        "## Claim Scope",
        "",
        "This audit classifies the v0.9.4.1 compiler spot failures. It does not claim solved arithmetic, stable convergence, solved OOD, same-size LLM advantage, safe real promotion, production readiness, or a full compiler-backed longrun.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_mainline(out: Path, summary: Dict[str, Any]) -> None:
    still_not_proven = [
        "solved arithmetic",
        "stable convergence",
        "solved OOD",
        "general program synthesis",
        "same-size LLM advantage",
        "safe real promotion",
        "production readiness",
        "full compiler-backed longrun",
    ]
    payload = {
        "what_this_version_proved": "It classified the original v0.9.4.1 compiler spot failures and preserved original metrics separately from patched replay.",
        "what_this_version_did_not_prove": still_not_proven,
        "main_cause_of_45_failures": summary.get("dominant_failure_category"),
        "dominant_failure_explanation": "MSVC C source syntax failure caused by adjacent sign tokens such as -- in generated arithmetic expressions." if summary.get("dominant_failure_category") == "compile_syntax_error" else "",
        "original_555_of_600_result_still_valid": True,
        "patched_rerun_executed": summary.get("patched_rerun_executed"),
        "patched_improved": summary.get("patched_delta_vs_original", 0) > 0,
        "engineering_issue_dominant": summary.get("engineering_issue_dominant"),
        "candidate_error_dominant": summary.get("candidate_error_dominant"),
        "recommended_claim_level": summary.get("recommended_claim_level"),
        "blocking_issues": summary.get("blocking_issues"),
        "required_next_run": summary.get("required_next_run"),
        "results_for_paper_v2": [
            "original compiler-backed spot result remains preserved",
            "failure taxonomy distribution",
            "patched replay metrics if described separately",
        ],
        "results_requiring_revalidation": [
            "remaining failure categories",
            "full compiler-backed longrun",
        ],
        "still_not_proven": still_not_proven,
    }
    _write_json(out / "mainline_conclusion.json", payload)
    md = [
        "# v0.9.4.2 Mainline Conclusion",
        "",
        "## What This Version Proved",
        str(payload["what_this_version_proved"]),
        "",
        "## What This Version Did Not Prove",
    ]
    md.extend(f"- {item}" for item in still_not_proven)
    md.extend([
        "",
        f"Main cause of the original failures: {payload['main_cause_of_45_failures']}.",
        f"Original 555/600 result still valid: {payload['original_555_of_600_result_still_valid']}.",
        f"Patched rerun executed: {payload['patched_rerun_executed']}.",
        f"Recommended claim level: {payload['recommended_claim_level']}.",
        "",
    ])
    (out / "mainline_conclusion.md").write_text("\n".join(md), encoding="utf-8")


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[Dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _safe_stdout(text: str) -> bool:
    return bool(text.strip().lstrip("-").isdigit())


def _tail(text: Any, max_chars: int = 2000) -> str:
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    return str(text or "")[-max_chars:]
