from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def run_shadow_profile_review(source_records: str | Path, output_records: str | Path) -> Dict[str, object]:
    profile = json.loads((Path(source_records) / "shadow_profile_config.json").read_text(encoding="utf-8"))
    issues: List[str] = []
    checks = {
        "shadow_profile_valid": profile.get("shadow_profile_created") is True and profile.get("profile_name") == "production_shadow_dry_run_v1_0_6",
        "explicit_opt_in_confirmed": profile.get("explicitly_opt_in") is True,
        "default_profile_false_confirmed": profile.get("default_profile") is False,
        "real_promotion_false_confirmed": profile.get("real_promotion_enabled") is False,
        "user_facing_false_confirmed": profile.get("user_facing_enabled") is False,
        "rollback_required_confirmed": profile.get("rollback_required") is True,
        "audit_trace_required_confirmed": profile.get("audit_trace_required") is True,
    }
    issues = [key for key, passed in checks.items() if not passed]
    result = {
        "shadow_profile_review_completed": True,
        **checks,
        "shadow_profile_review_issues": issues,
    }
    _write_json(Path(output_records) / "shadow_profile_review.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
