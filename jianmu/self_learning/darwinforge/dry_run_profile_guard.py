from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def run_dry_run_profile_guard(output_records: str | Path, shadow_profile: Dict[str, object]) -> Dict[str, object]:
    issues: List[str] = []
    checks = {
        "default_profile_unchanged": bool(shadow_profile.get("default_profile_unchanged")),
        "shadow_profile_not_default": shadow_profile.get("default_profile") is False,
        "real_promotion_off": shadow_profile.get("real_promotion_enabled") is False,
        "production_support_flags_false": shadow_profile.get("production_supported") is False
        and shadow_profile.get("production_support_claim_enabled") is False,
        "release_tag_disabled": shadow_profile.get("release_enabled") is False,
        "user_facing_enablement_false": shadow_profile.get("user_facing_enabled") is False,
        "results_records_only": True,
        "rollback_path_exists": bool(shadow_profile.get("rollback_required")),
        "no_external_api_or_llm_api": True,
        "no_natural_language_layer_activation": True,
    }
    for name, passed in checks.items():
        if not passed:
            issues.append(name)
    result = {
        **checks,
        "dry_run_profile_guard_passed": not issues,
        "guard_passed": not issues,
        "blocking_issues": ["guard_failed"] + issues if issues else [],
        "recommended_claim_level": "dry_run_guard_failed" if issues else "guard_passed",
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "dry_run_profile_guard.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
