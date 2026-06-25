from __future__ import annotations

import json
from pathlib import Path

from jianmu.self_learning.darwinforge.opt_live_display_schema import STILL_NOT_PROVEN_OPT_TRUE8H


def build_opt_true8h_readiness(output_records: str | Path, payload: dict) -> dict:
    out = Path(output_records)
    blocking = []
    if not payload.get("opt_display_smoke_gate_passed"):
        blocking.append("opt_display_gate_failed")
        level = "opt_display_gate_failed"
    elif not payload.get("git_storm_guard_passed"):
        blocking.append("git_storm_guard_failed")
        level = "backend_validation_blocked_by_git_storm"
    elif not payload.get("memory_queue_guard_passed") and not payload.get("memory_guard_passed"):
        blocking.append("memory_queue_guard_failed")
        level = "backend_validation_blocked_by_memory_guard"
    elif payload.get("security_interference_detected_count", 0) > 0:
        blocking.append("security_interference_detected")
        level = "backend_validation_blocked_by_security_interference"
    elif payload.get("true8h_backend_validation_passed"):
        level = "opt_display_recovered_true8h_backend_validated"
    elif payload.get("true8h_validation_started"):
        level = "opt_display_recovered_backend_validation_partial"
    else:
        level = "failed"
    result = {
        **payload,
        "opt_display_gate_completed": True,
        "v1_0_8_8_old_compiler_claim_accepted": False,
        "v1_0_8_8_old_compiler_claim_downgraded": True,
        "real_compile_lane_integrity_repaired": bool(payload.get("true8h_backend_validation_passed")),
        "default_profile_unchanged": True,
        "real_promotion_enabled": False,
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "redqueen_autonomous_governance_completed": False,
        "ready_for_official_release": False,
        "recommended_claim_level": level,
        "blocking_issues": blocking,
        "required_next_run": "Human review of OPT display and true 8h backend compiler evidence before any claim expansion.",
        "still_not_proven": list(STILL_NOT_PROVEN_OPT_TRUE8H),
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "opt_true8h_readiness.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
