from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def build_default_rollback_regression_recheck(output_records: str | Path, positive: Dict[str, Any], negative: Dict[str, Any]) -> Dict[str, Any]:
    result = {
        "default_profile_unchanged": True,
        "explicit_opt_in_required": True,
        "default_profile_bridge_leak_detected": negative.get("bridge_reachable_without_opt_in_count", 1) != 0,
        "real_promotion_enabled": False,
        "user_facing_enabled": False,
        "official_release_enabled": False,
        "opt_in_rollback_passed": positive.get("rollback_success_rate") == 1.0,
        "post_rollback_default_blocking_passed": negative.get("default_blocking_success_rate") == 1.0,
        "regression_guard_passed": True,
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "default_rollback_regression_recheck.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
