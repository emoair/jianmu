from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List


CATEGORIES = [
    "permission_write_c_source",
    "permission_compile_spawn",
    "permission_compile_output_obj",
    "permission_compile_output_exe",
    "permission_run_exe",
    "permission_read_stdout",
    "permission_cleanup_c_file",
    "permission_cleanup_obj_file",
    "permission_cleanup_exe_file",
    "permission_cleanup_temp_dir",
    "process_spawn_error",
    "cl_or_link_toolchain_error",
    "compile_syntax_error",
    "compile_type_error",
    "runtime_error",
    "runtime_timeout",
    "wrong_stdout",
    "candidate_mapping_error",
    "freeze_prune_transfer_error",
    "trace_or_recording_error",
    "antivirus_or_defender_lock_suspected",
    "environment_interference_suspected",
    "unknown",
]


def classify_layerwise_compiler_failure(row: Dict[str, Any]) -> str:
    stage = str(row.get("permission_error_stage") or "").lower()
    exc = str(row.get("exception_type") or "").lower()
    notes = str(row.get("notes") or "").lower()
    stderr = str(row.get("compile_stderr_tail") or "").lower()
    message = str(row.get("exception_message_tail") or "").lower()
    if "permissionerror" in exc:
        if "cleanup_temp" in stage:
            return "permission_cleanup_temp_dir"
        if "compile_spawn" in stage:
            return "permission_compile_spawn"
        if "run_exe" in stage:
            return "permission_run_exe"
        if "write_c" in stage:
            return "permission_write_c_source"
        return "environment_interference_suspected"
    if row.get("cleanup_failure_count", 0):
        return "permission_cleanup_temp_dir" if row.get("cleanup_permission_error") else "trace_or_recording_error"
    if row.get("timeout") or "timeoutexpired" in exc:
        return "runtime_timeout" if row.get("compile_success") else "cl_or_link_toolchain_error"
    if "filenotfounderror" in exc:
        return "process_spawn_error" if not row.get("compile_success") else "environment_interference_suspected"
    if row.get("compile_returncode") not in (None, 0):
        if "syntax error" in stderr or "c2143" in stderr:
            return "compile_syntax_error"
        if "type" in stderr or "c2440" in stderr:
            return "compile_type_error"
        return "cl_or_link_toolchain_error"
    if row.get("runtime_returncode") not in (None, 0):
        return "runtime_error"
    if row.get("compile_success") and row.get("runtime_success") and not row.get("compiler_verified_correct"):
        return "wrong_stdout"
    if "candidate_mapping" in notes or "mapping" in message:
        return "candidate_mapping_error"
    if "freeze" in notes or "prune" in notes or "transfer" in notes:
        return "freeze_prune_transfer_error"
    return "unknown"


def load_layerwise_failures(source_records: str | Path) -> List[Dict[str, Any]]:
    source = Path(source_records)
    path = source / "compiler_validation_trace_layerwise_sparse_1B_freeze_prune.jsonl"
    failures: List[Dict[str, Any]] = []
    if not path.exists():
        return failures
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("compiler_invoked") and not row.get("compiler_verified_correct"):
            row["failure_category"] = classify_layerwise_compiler_failure(row)
            failures.append(row)
    return failures


def build_layerwise_compiler_failure_taxonomy(source_records: str | Path, output_records: str | Path, environment_issue_suspected: bool = False) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    metrics_path = Path(source_records) / "compiler_validation_metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
    layer_metrics = metrics.get("per_profile", {}).get("layerwise_sparse_1B_freeze_prune", {})
    failures = load_layerwise_failures(source_records)
    distribution = Counter(row["failure_category"] for row in failures)
    dominant = distribution.most_common(1)[0][0] if distribution else "none"
    candidate_categories = {"wrong_stdout", "candidate_mapping_error", "compile_syntax_error", "compile_type_error"}
    freeze_categories = {"freeze_prune_transfer_error"}
    engineering_categories = {"permission_compile_spawn", "permission_run_exe", "permission_cleanup_temp_dir", "process_spawn_error", "cl_or_link_toolchain_error", "runtime_timeout", "environment_interference_suspected"}
    result = {
        "taxonomy_completed": bool(metrics_path.exists()),
        "original_validation_sample_count": layer_metrics.get("real_compiler_invocation_count", 0),
        "original_success_count": layer_metrics.get("compiler_verified_correct_count", 0),
        "original_failure_count": layer_metrics.get("compiler_verified_failure_count", len(failures)),
        "classified_failure_count": len(failures),
        "unknown_failure_count": distribution.get("unknown", 0),
        "unknown_failure_explanation": "" if distribution.get("unknown", 0) == 0 else "Original trace lacked enough process/stderr detail for these rows.",
        "failure_category_distribution": {name: distribution.get(name, 0) for name in CATEGORIES if distribution.get(name, 0)},
        "dominant_failure_category": dominant,
        "engineering_issue_dominant": dominant in engineering_categories,
        "candidate_error_dominant": dominant in candidate_categories,
        "freeze_prune_error_dominant": dominant in freeze_categories,
        "environment_issue_suspected": bool(environment_issue_suspected or dominant in {"permission_compile_spawn", "permission_run_exe", "process_spawn_error", "cl_or_link_toolchain_error", "runtime_timeout"}),
    }
    _write_json(out / "layerwise_compiler_failure_taxonomy.json", result)
    _write_examples(out / "layerwise_compiler_failure_examples.jsonl", failures)
    (out / "layerwise_compiler_failure_taxonomy.md").write_text(_render_md(result), encoding="utf-8")
    return result


def _write_examples(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    counts: Counter[str] = Counter()
    lines: List[str] = []
    for row in rows:
        cat = row.get("failure_category", "unknown")
        if counts[cat] >= 50:
            continue
        counts[cat] += 1
        safe = {key: row.get(key) for key in ["sample_id_hash", "stage", "category", "failure_category", "exception_type", "permission_error_stage", "compile_returncode", "runtime_returncode", "timeout", "compile_stderr_tail", "runtime_stderr_tail"]}
        lines.append(json.dumps(safe, ensure_ascii=False, sort_keys=True))
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _render_md(result: Dict[str, Any]) -> str:
    lines = ["# Layerwise Compiler Failure Taxonomy", ""]
    for key in ["original_validation_sample_count", "original_success_count", "original_failure_count", "classified_failure_count", "unknown_failure_count", "dominant_failure_category", "engineering_issue_dominant", "candidate_error_dominant", "freeze_prune_error_dominant", "environment_issue_suspected"]:
        lines.append(f"- {key}: {result.get(key)}")
    lines.append("")
    lines.append("## Distribution")
    for key, value in result.get("failure_category_distribution", {}).items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines) + "\n"


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
