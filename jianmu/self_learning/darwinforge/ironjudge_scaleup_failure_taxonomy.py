from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable


CATEGORIES = [
    "permission_write_c_source",
    "permission_compile_spawn",
    "permission_compile_output_obj",
    "permission_compile_output_exe",
    "permission_run_exe",
    "permission_read_stdout",
    "permission_cleanup_temp_dir",
    "process_spawn_error",
    "cl_or_link_toolchain_error",
    "compile_syntax_error",
    "compile_type_error",
    "runtime_error",
    "runtime_timeout",
    "wrong_stdout",
    "candidate_mapping_error",
    "target_ir_error",
    "frontier_ir_lowering_error",
    "boundary_compiler_misroute",
    "unsupported_feature_misroute",
    "trace_or_recording_error",
    "environment_interference_suspected",
    "unknown",
]


def write_failure_taxonomy(output_records: str | Path, traces: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    distribution = {name: 0 for name in CATEGORIES}
    examples = []
    for row in traces:
        if not row.get("compiler_invoked") or row.get("compiler_verified_correct"):
            continue
        category = _classify(row)
        distribution[category] += 1
        if len(examples) < 100:
            examples.append({"sample_id_hash": row.get("sample_id_hash"), "failure_category": category, "level_name": row.get("level_name")})
    failure_count = sum(distribution.values())
    result = {
        "failure_count": failure_count,
        "unknown_failure_count": distribution["unknown"],
        "failure_category_distribution": distribution,
        "engineering_issue_dominant": sum(distribution[k] for k in ["permission_compile_spawn", "process_spawn_error", "cl_or_link_toolchain_error", "runtime_timeout"]) > failure_count / 2 if failure_count else False,
        "candidate_error_dominant": distribution["candidate_mapping_error"] > failure_count / 2 if failure_count else False,
        "frontier_lowering_error_dominant": distribution["frontier_ir_lowering_error"] > failure_count / 2 if failure_count else False,
        "boundary_error_dominant": distribution["boundary_compiler_misroute"] + distribution["unsupported_feature_misroute"] > failure_count / 2 if failure_count else False,
    }
    out = Path(output_records)
    _write_json(out / "ironjudge_failure_taxonomy.json", result)
    (out / "ironjudge_failure_examples.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in examples), encoding="utf-8")
    (out / "ironjudge_failure_taxonomy.md").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def _classify(row: Dict[str, Any]) -> str:
    if row.get("permission_error") or row.get("exception_type") == "PermissionError":
        return "permission_compile_spawn"
    if row.get("timeout"):
        return "runtime_timeout"
    if row.get("compile_success") is False:
        return "compile_syntax_error"
    if row.get("runtime_success") is False:
        return "runtime_error"
    if row.get("compiler_invoked") and not row.get("compiler_verified_correct"):
        return "wrong_stdout"
    return "unknown"


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
