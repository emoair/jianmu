from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from jianmu.self_learning.darwinforge.compiler_integrity_schema import STILL_NOT_PROVEN_COMPILER_INTEGRITY


def build_compiler_integrity_readiness(output_records: str | Path, payload: Dict[str, object]) -> Dict[str, object]:
    blocking = []
    if not payload.get("backend_validation_passed"):
        blocking.append("backend_validation_failed")
        level = "compiler_integrity_blocked_by_backend_validation"
    elif payload.get("security_interference_detected_count", 0) > 0:
        level = "compiler_integrity_repaired_with_security_notes"
    elif all([
        payload.get("compiler_integrity_audit_completed"),
        payload.get("v1_0_8_8_compiler_claim_downgraded") or payload.get("v1_0_8_8_compiler_claim_accepted"),
        payload.get("frontend_backend_lane_separated"),
        payload.get("backend_manifest_contract_passed"),
        payload.get("opt_display_recovery_passed"),
        payload.get("backend_replay_passed"),
        payload.get("default_profile_unchanged"),
        not payload.get("real_promotion_enabled"),
    ]):
        level = "compiler_invocation_integrity_repaired_and_validated"
    else:
        blocking.append("compiler_integrity_threshold_not_met")
        level = "failed"
    result = {
        **payload,
        "recommended_claim_level": level,
        "blocking_issues": blocking,
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "redqueen_autonomous_governance_completed": False,
        "ready_for_official_release": False,
        "real_promotion_enabled": False,
        "default_profile_unchanged": True,
        "required_next_run": "Human review of compiler invocation integrity evidence before using backend invocation counts in longer governance claims.",
        "still_not_proven": list(STILL_NOT_PROVEN_COMPILER_INTEGRITY),
    }
    _write_json(Path(output_records) / "compiler_integrity_readiness.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

