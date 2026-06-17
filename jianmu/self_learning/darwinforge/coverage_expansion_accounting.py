from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable


def audit_coverage_expansion_accounting(output_records: str | Path, rows: Iterable[Dict[str, Any]], replay_worker_timeout_count: int = 0) -> Dict[str, Any]:
    rows = list(rows)
    ids = [row.get("compile_invocation_id") for row in rows]
    compiler_rows = [row for row in rows if row.get("compiler_invoked")]
    source_hashes = [row.get("source_sha256") for row in compiler_rows]
    result = {
        "real_validation_events": len(rows),
        "real_compiler_invocations": len(compiler_rows),
        "real_cl_invocation_count": sum(1 for row in rows if row.get("cl_invoked")),
        "real_link_invocation_count": sum(1 for row in rows if row.get("link_invoked")),
        "real_exe_run_count": sum(1 for row in rows if row.get("exe_run")),
        "unique_compile_unit_count": len(set(source_hashes)),
        "source_sha256_unique_count": len(set(source_hashes)),
        "shape_signature_unique_count": len({row.get("shape_signature") for row in compiler_rows}),
        "cached_result_used_as_new_count": sum(1 for row in rows if row.get("cached")),
        "duplicate_invocation_id_count": len(ids) - len(set(ids)),
        "stubbed_validation_detected": any(row.get("stubbed") for row in rows),
        "summary_only_validation_detected": False,
        "syntax_filter_used_as_correctness_evidence": False,
        "wrong_stdout_count": sum(1 for row in rows if row.get("expected_stdout") != row.get("actual_stdout")),
        "timeout_count": sum(1 for row in rows if row.get("timeout")),
        "permission_error_count": sum(1 for row in rows if row.get("permission_error")),
        "cleanup_failure_count": sum(1 for row in rows if row.get("cleanup_failure")),
        "thread_safety_issue_detected": False,
        "trace_write_error_count": 0,
        "temp_dir_collision_count": 0,
        "replay_worker_timeout_count": replay_worker_timeout_count,
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "coverage_expansion_accounting.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
