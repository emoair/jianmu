from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from jianmu.self_learning.darwinforge.time_integrity_schema import TIME_REPAIR_STILL_NOT_PROVEN


def build_time_integrity_readiness(output_records: str | Path, payload: Dict[str, object]) -> Dict[str, object]:
    blocking = []
    if not payload.get("code_audit_passed_after_fix"):
        blocking.append("code_audit_failed")
        level = "time_integrity_blocked_by_code_audit"
    elif not payload.get("repair_validation_passed"):
        blocking.append("wallclock_validation_incomplete")
        level = "time_integrity_repaired_but_validation_partial"
    elif payload.get("v1_0_8_6_endurance_claim_accepted"):
        level = "v1_0_8_6_endurance_claim_verified"
    elif all([
        payload.get("v1_0_8_6_time_claim_audited"),
        payload.get("wallclock_timer_contract_passed"),
        payload.get("heartbeat_contract_passed"),
        payload.get("time_integrity_guard_passed"),
        payload.get("repair_validation_passed"),
        payload.get("actual_elapsed_seconds", 0) >= 7200,
        payload.get("lifecycle_recheck_passed", payload.get("lifecycle_clean", False)),
        payload.get("default_profile_unchanged"),
        not payload.get("real_promotion_enabled"),
        not payload.get("production_function_support_completed"),
        not payload.get("production_array_support_completed"),
        not payload.get("production_recursion_support_completed"),
    ]):
        level = "time_integrity_repaired_and_short_wallclock_validated"
    elif payload.get("v1_0_8_6_endurance_claim_downgraded"):
        level = "v1_0_8_6_endurance_claim_downgraded"
    else:
        blocking.append("time_integrity_threshold_not_met")
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
        "redqueen_multiround_stability_positive": False,
        "required_next_run": "Run a true 8h RedQueen stability validation with monotonic timing evidence before restoring any 8h stability claim.",
        "still_not_proven": list(TIME_REPAIR_STILL_NOT_PROVEN),
    }
    _write_json(Path(output_records) / "time_integrity_readiness.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
