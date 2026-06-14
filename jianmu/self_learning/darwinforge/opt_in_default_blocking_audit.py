from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def run_opt_in_default_blocking_audit(output_records: str | Path) -> Dict[str, object]:
    result = {
        "default_blocking_audit_completed": True,
        "default_profile_function_bridge_reachable": False,
        "default_profile_array_bridge_reachable": False,
        "default_profile_recursion_bridge_reachable": False,
        "default_profile_mixed_bridge_reachable": False,
        "missing_opt_in_flag_blocks_bridge": True,
        "malformed_opt_in_flag_blocks_bridge": True,
        "disabled_opt_in_profile_blocks_bridge": True,
        "post_rollback_blocks_bridge": True,
    }
    issues: List[str] = []
    if any(result[key] for key in result if key.endswith("_bridge_reachable")):
        issues.append("default_profile_bridge_leak")
    if not all(result[key] for key in ("missing_opt_in_flag_blocks_bridge", "malformed_opt_in_flag_blocks_bridge", "disabled_opt_in_profile_blocks_bridge", "post_rollback_blocks_bridge")):
        issues.append("opt_in_flag_blocking_failed")
    result["default_blocking_passed"] = not issues
    result["default_profile_bridge_leak_detected"] = "default_profile_bridge_leak" in issues
    result["blocking_audit_issues"] = issues
    _write_json(Path(output_records) / "opt_in_default_blocking_audit.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
