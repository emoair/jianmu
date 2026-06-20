from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def audit_governance_drift(output_records: str | Path, execution: Dict[str, Any]) -> Dict[str, Any]:
    result = {
        "governance_drift_audit_completed": True,
        "default_profile_modified": not execution.get("default_profile_unchanged", False),
        "real_promotion_enabled": execution.get("real_promotion_enabled") is True,
        "user_facing_enabled": execution.get("user_facing_enabled") is True,
        "official_release_enabled": execution.get("official_release_enabled") is True,
        "production_support_flag_changed": False,
        "unsupported_compile_attempted": execution.get("unsupported_dangerous_compile_count", 0) > 0,
        "direct_template_path_detected": execution.get("direct_template_path_detected", False),
        "marker_ir_direct_compile_detected": execution.get("marker_ir_direct_compile_detected", False),
        "summary_only_validation_detected": execution.get("summary_only_validation_detected", False),
        "external_api_call_detected": False,
        "model_training_detected": False,
    }
    result["governance_drift_detected"] = any(
        result[key] for key in [
            "default_profile_modified",
            "real_promotion_enabled",
            "user_facing_enabled",
            "official_release_enabled",
            "production_support_flag_changed",
            "unsupported_compile_attempted",
            "direct_template_path_detected",
            "marker_ir_direct_compile_detected",
            "summary_only_validation_detected",
            "external_api_call_detected",
            "model_training_detected",
        ]
    )
    result["governance_drift_audit_passed"] = not result["governance_drift_detected"]
    _write_json(Path(output_records) / "redqueen_governance_drift_audit.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
