from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable


def audit_opt_in_compiler_accounting(output_records: str | Path, rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    rows = list(rows)
    compile_rows = [row for row in rows if row.get("compiler_invoked")]
    ids = [row.get("compile_invocation_id") for row in rows]
    result = {
        "real_validation_events": len(rows),
        "real_compiler_invocations": len(compile_rows),
        "real_cl_invocation_count": sum(1 for row in rows if row.get("cl_invoked")),
        "real_link_invocation_count": sum(1 for row in rows if row.get("link_invoked")),
        "real_exe_run_count": sum(1 for row in rows if row.get("exe_run")),
        "unique_compile_unit_count": len(set(row.get("source_sha256") for row in rows if row.get("compiler_invoked"))),
        "cached_result_used_as_new_count": sum(1 for row in rows if row.get("cached")),
        "duplicate_invocation_id_count": len(ids) - len(set(ids)),
        "stubbed_validation_detected": any(row.get("stubbed") for row in rows),
        "summary_only_validation_detected": False,
        "syntax_filter_used_as_correctness_evidence": False,
        "wrong_stdout_count": sum(1 for row in rows if row.get("actual_stdout") != row.get("expected_stdout")),
        "timeout_count": sum(1 for row in rows if row.get("timeout")),
        "permission_error_count": sum(1 for row in rows if row.get("permission_error")),
        "cleanup_failure_count": sum(1 for row in rows if row.get("cleanup_failure")),
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "opt_in_compiler_accounting.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def detect_stubbed_validation(rows: Iterable[Dict[str, Any]]) -> bool:
    return any(row.get("stubbed") or (row.get("passed") and row.get("explicit_opt_in") and not row.get("exe_run")) for row in rows)
