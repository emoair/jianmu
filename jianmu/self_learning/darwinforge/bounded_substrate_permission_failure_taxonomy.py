from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


PERMISSION_CATEGORIES = [
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
    "permission_trace_write",
    "temp_path_collision",
    "path_quoting_error",
    "path_length_error",
    "one_drive_or_sync_lock_suspected",
    "antivirus_or_defender_lock_suspected",
    "process_handle_not_released",
    "compile_syntax_error",
    "compile_type_error",
    "runtime_error",
    "runtime_timeout",
    "wrong_output",
    "trace_or_recording_error",
    "unknown",
]


def classify_v0_9_7_1_failures(source_records: str | Path, output_records: str | Path) -> Dict[str, Any]:
    source = Path(source_records)
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    failures_path = source / "compiler_validation_failures.jsonl"
    if not failures_path.exists():
        result = {"taxonomy_completed": False, "missing_source_records": True, "recommended_claim_level": "failed"}
        _write_json(out / "permission_failure_taxonomy.json", result)
        return result
    failures = _read_jsonl(failures_path)
    examples: List[Dict[str, Any]] = []
    distribution: Dict[str, int] = {name: 0 for name in PERMISSION_CATEGORIES}
    for row in failures:
        category = classify_failure_row(row)
        distribution[category] = distribution.get(category, 0) + 1
        examples.append({
            "sample_id_hash": row.get("sample_id_hash"),
            "stage": row.get("stage"),
            "category": row.get("category"),
            "failure_category": category,
            "original_notes": row.get("notes", ""),
            "compiler_invoked": row.get("compiler_invoked", False),
            "latency_ms": row.get("latency_ms", 0.0),
        })
    distribution = {k: v for k, v in distribution.items() if v}
    dominant = max(distribution, key=distribution.get) if distribution else "unknown"
    engineering = dominant in {
        "permission_cleanup_temp_dir",
        "process_handle_not_released",
        "one_drive_or_sync_lock_suspected",
        "antivirus_or_defender_lock_suspected",
        "permission_compile_spawn",
        "permission_write_c_source",
    }
    result = {
        "taxonomy_completed": True,
        "original_failure_count": len(failures),
        "classified_failure_count": len(examples),
        "unknown_failure_count": distribution.get("unknown", 0),
        "failure_category_distribution": distribution,
        "dominant_failure_category": dominant,
        "engineering_issue_dominant": engineering,
        "candidate_error_dominant": dominant in {"compile_syntax_error", "compile_type_error", "runtime_error", "wrong_output"},
        "notes": "v0.9.7.1 failures occurred after long latency with compiler_invoked=false, consistent with temp-dir cleanup/process-handle PermissionError being caught by the outer validator",
    }
    _write_json(out / "permission_failure_taxonomy.json", result)
    (out / "permission_failure_taxonomy.md").write_text(_render_taxonomy_md(result), encoding="utf-8")
    (out / "permission_failure_examples.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in examples), encoding="utf-8")
    return result


def classify_failure_row(row: Dict[str, Any]) -> str:
    note = str(row.get("notes", "")).lower()
    if "permissionerror" in note and not row.get("compiler_invoked") and row.get("latency_ms", 0) > 1000:
        return "permission_cleanup_temp_dir"
    if "permissionerror" in note and not row.get("compiler_invoked"):
        return "permission_compile_spawn"
    if row.get("timeout"):
        return "runtime_timeout"
    if row.get("compile_returncode") not in (None, 0):
        return "compile_syntax_error"
    if row.get("runtime_returncode") not in (None, 0):
        return "runtime_error"
    if row.get("runtime_success") and not row.get("compiler_verified_correct"):
        return "wrong_output"
    return "unknown"


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _render_taxonomy_md(result: Dict[str, Any]) -> str:
    lines = ["# Bounded Substrate Permission Failure Taxonomy", ""]
    lines.append(f"taxonomy_completed: {result['taxonomy_completed']}")
    lines.append(f"dominant_failure_category: {result.get('dominant_failure_category')}")
    lines.append("")
    for key, value in result.get("failure_category_distribution", {}).items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines) + "\n"
