from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def audit_scale_compiler_accounting(output_records: str | Path, rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    rows = list(rows)
    ids = [row.get("compile_invocation_id") for row in rows]
    duplicate = len(ids) - len(set(ids))
    result = {
        "real_compiler_invocations": sum(1 for row in rows if row.get("cl_invoked") or row.get("compiler_invoked")),
        "real_cl_invocation_count": sum(1 for row in rows if row.get("cl_invoked")),
        "real_link_invocation_count": sum(1 for row in rows if row.get("link_invoked")),
        "real_exe_run_count": sum(1 for row in rows if row.get("exe_run")),
        "unique_compile_unit_count": len(set(row.get("source_sha256") for row in rows)),
        "cached_result_used_as_new_count": sum(1 for row in rows if row.get("cached")),
        "duplicate_invocation_id_count": duplicate,
        "stubbed_validation_detected": any(row.get("stubbed") for row in rows),
        "summary_only_validation_detected": False,
        "syntax_filter_used_as_correctness_evidence": False,
        "timeout_count": sum(1 for row in rows if row.get("timeout")),
        "wrong_stdout_count": sum(1 for row in rows if row.get("actual_stdout") != row.get("expected_stdout")),
        "permission_error_count": sum(1 for row in rows if row.get("permission_error")),
        "cleanup_failure_count": sum(1 for row in rows if row.get("cleanup_failure")),
    }
    Path(output_records).mkdir(parents=True, exist_ok=True)
    (Path(output_records) / "scale_compiler_accounting_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result

