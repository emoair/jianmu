from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.controlled_opt_in_approval_schema import STILL_NOT_PROVEN


def build_controlled_opt_in_approval_readiness(output_records: str | Path, verdict: Dict[str, Any], isolation: Dict[str, Any]) -> Dict[str, Any]:
    status = verdict.get("approval_status")
    if status == "approval_recommended":
        level = "controlled_opt_in_support_approval_recommended"
    elif status == "approved":
        level = "controlled_opt_in_support_approved"
    elif status == "approved_with_notes":
        level = "controlled_opt_in_support_approved_with_notes"
    elif status == "blocked_by_records_isolation":
        level = "approval_blocked_by_records_isolation"
    elif status == "blocked_by_scope_overclaim":
        level = "approval_blocked_by_scope_overclaim"
    elif status == "blocked_by_unsupported_boundary_gap":
        level = "approval_blocked_by_unsupported_boundary_gap"
    elif status == "blocked_by_evidence_sampling":
        level = "approval_blocked_by_evidence_sampling"
    else:
        level = "failed"
    result = {
        "approval_review_started": True,
        "approval_review_completed": True,
        "no_model_training": True,
        "no_weight_update": True,
        "reused_existing_logic": True,
        "staged_opt_in_enabled": True,
        **verdict,
        "isolation_fix_applied": isolation.get("isolation_fix_applied"),
        "tests_write_real_records_detected": isolation.get("tests_write_real_records_detected"),
        "historical_records_write_detected": isolation.get("historical_records_write_detected"),
        "ready_for_official_release": False,
        "recommended_claim_level": level,
        "required_next_run": "human signoff or next controlled opt-in governance review; do not claim production support completed",
        "still_not_proven": list(STILL_NOT_PROVEN),
    }
    path = Path(output_records) / "controlled_opt_in_approval_readiness.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
