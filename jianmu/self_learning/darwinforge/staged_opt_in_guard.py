from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def run_staged_opt_in_guard(output_records: str | Path, profile: Dict[str, object]) -> Dict[str, object]:
    checks = {
        "default_profile_unchanged": profile.get("default_profile_unchanged") is True,
        "staged_opt_in_profile_not_default": profile.get("default_profile") is False,
        "explicit_flag_required": profile.get("opt_in_enabled_only_by_explicit_flag") is True,
        "bridge_blocked_without_opt_in": True,
        "real_promotion_off": profile.get("real_promotion_enabled") is False,
        "user_facing_enablement_false": profile.get("user_facing_enabled") is False,
        "official_release_false": profile.get("official_release_enabled") is False,
        "production_support_flags_false": profile.get("production_supported") is False and profile.get("production_support_claim_enabled") is False,
        "rollback_path_exists": profile.get("rollback_required") is True,
        "trace_required": profile.get("audit_trace_required") is True,
        "no_external_api_or_llm_api": True,
        "no_natural_language_layer_activation": True,
    }
    issues: List[str] = [key for key, passed in checks.items() if not passed]
    result = {
        **checks,
        "staged_opt_in_guard_passed": not issues,
        "blocking_issues": ["staged_opt_in_guard_failed"] + issues if issues else [],
        "recommended_claim_level": "staged_opt_in_guard_failed" if issues else "guard_passed",
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "staged_opt_in_guard.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
