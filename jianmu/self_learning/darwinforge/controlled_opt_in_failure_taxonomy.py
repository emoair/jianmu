from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


FAILURE_TYPES = (
    ("default_blocked", "info"),
    ("malformed_opt_in_blocked", "info"),
    ("disabled_profile_blocked", "info"),
    ("unsupported_policy_rejected", "warning"),
    ("unsupported_shape_rejected", "warning"),
    ("compiler_failure", "blocking"),
    ("stdout_mismatch", "blocking"),
    ("timeout", "blocking"),
    ("rollback_failure", "blocking"),
    ("trace_write_failure", "blocking"),
    ("replay_drift", "blocking"),
    ("default_profile_contamination", "blocking"),
    ("template_bypass_detected", "blocking"),
    ("marker_ir_direct_compile_detected", "blocking"),
    ("summary_only_validation_detected", "blocking"),
)


def build_failure_taxonomy(output_records: str | Path) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for failure_type, severity in FAILURE_TYPES:
        rows.append(
            {
                "failure_type": failure_type,
                "severity": severity,
                "expected_action": _action(failure_type, severity),
                "trace_required": True,
                "support_candidate_impact": "blocks candidate" if severity == "blocking" else "record and classify",
                "production_claim_allowed": False,
            }
        )
    result = {"failure_taxonomy_generated": True, "failures": rows}
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "failure_taxonomy.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _action(failure_type: str, severity: str) -> str:
    if severity == "blocking":
        return f"stop or downgrade readiness; investigate {failure_type}"
    return f"classify {failure_type} and keep default profile blocked"
