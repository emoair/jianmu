from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


REQUIRED_FAILURES = (
    "default_blocked",
    "malformed_opt_in_blocked",
    "disabled_profile_blocked",
    "unsupported_policy_rejected",
    "unsupported_shape_rejected",
    "compiler_failure",
    "stdout_mismatch",
    "timeout",
    "rollback_failure",
    "trace_write_failure",
    "replay_drift",
    "default_profile_contamination",
    "template_bypass_detected",
    "marker_ir_direct_compile_detected",
    "summary_only_validation_detected",
)

BLOCKING_FAILURES = set(REQUIRED_FAILURES[5:])


def audit_failure_taxonomy_completeness(source_records: str | Path, output_records: str | Path) -> Dict[str, Any]:
    data = json.loads((Path(source_records) / "failure_taxonomy.json").read_text(encoding="utf-8"))
    rows = data.get("failures", [])
    by_type = {str(row.get("failure_type")): row for row in rows}
    missing = [item for item in REQUIRED_FAILURES if item not in by_type]
    blocking_ok = all(by_type.get(item, {}).get("severity") == "blocking" for item in BLOCKING_FAILURES if item in by_type)
    production_claim = any(row.get("production_claim_allowed") is True for row in rows)
    result = {
        "failure_taxonomy_audit_completed": True,
        "required_failure_type_count": len(REQUIRED_FAILURES),
        "present_failure_type_count": len(set(by_type) & set(REQUIRED_FAILURES)),
        "missing_failure_types": missing,
        "blocking_failure_types_marked_blocking": blocking_ok,
        "production_claim_allowed_anywhere": production_claim,
        "failure_taxonomy_audit_passed": not missing and blocking_ok and not production_claim,
    }
    _write_json(Path(output_records) / "failure_taxonomy_completeness_audit.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
