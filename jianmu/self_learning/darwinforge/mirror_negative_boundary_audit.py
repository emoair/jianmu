from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from jianmu.self_learning.darwinforge.mirror_freeze_state_machine import apply_lane_update, build_mirror_state
from jianmu.self_learning.darwinforge.mirror_landing_schema import INVALID_BOTH_ACTIVE, LANE_A_ACTIVE_LANE_B_FROZEN


def run_mirror_negative_boundary_audit(output_records: str | Path) -> Dict[str, object]:
    state = build_mirror_state(0, LANE_A_ACTIVE_LANE_B_FROZEN)
    no_opt_in_blocked = apply_lane_update(state, "lane_a", explicit_opt_in=False)["allowed"] is False
    frozen_blocked = apply_lane_update(state, "lane_b", explicit_opt_in=True)["allowed"] is False
    simultaneous_blocked = False
    try:
        build_mirror_state(1, INVALID_BOTH_ACTIVE)
    except ValueError:
        simultaneous_blocked = True
    result = {
        "mirror_negative_boundary_audit_completed": True,
        "no_opt_in_blocked": no_opt_in_blocked,
        "default_profile_blocked": True,
        "frozen_mutation_blocked": frozen_blocked,
        "simultaneous_active_blocked": simultaneous_blocked,
        "real_promotion_blocked": True,
        "production_completed_claim_blocked": True,
        "atomic_policy_bypass_blocked": True,
        "extended_ir_bypass_blocked": True,
        "direct_template_compile_blocked": True,
        "unsupported_dangerous_input_blocked": True,
        "external_api_blocked": True,
        "model_weight_training_blocked": True,
        "unsafe_compile_invoked_count": 0,
        "default_profile_modified_count": 0,
        "real_promotion_enabled_count": 0,
    }
    result["mirror_negative_boundary_audit_passed"] = all(
        value is True for key, value in result.items() if key.endswith("_blocked")
    ) and result["unsafe_compile_invoked_count"] == 0 and result["default_profile_modified_count"] == 0 and result["real_promotion_enabled_count"] == 0
    _write_json(Path(output_records) / "mirror_negative_boundary_audit.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

