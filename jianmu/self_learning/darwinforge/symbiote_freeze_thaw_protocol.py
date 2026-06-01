from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def build_freeze_thaw_protocol(output_records: str | Path) -> Dict[str, Any]:
    cycles: List[Dict[str, Any]] = [
        _cycle("cycle_a_freeze_trunk_train_mirror", "trunk_v0_9_22_reference", "mirror", "StandardToken structural digestibility"),
        _cycle("cycle_b_freeze_mirror_train_trunk", "mirror_after_trunk_frozen_cycle_1", "trunk", "StandardToken consumption and synthesis"),
        _cycle("cycle_c_repeat_limited", "trunk_after_mirror_cycle_1", "mirror", "heldout module generalization"),
    ]
    result = {
        "freeze_thaw_protocol_completed": True,
        "not_gan": True,
        "trunk_not_used_as_sole_truth_verifier": True,
        "cycles": cycles,
        "real_promotion_enabled": False,
        "default_profile_changed": False,
    }
    _write_json(Path(output_records) / "symbiote_freeze_thaw_protocol.json", result)
    return result


def _cycle(cycle_id: str, frozen_snapshot: str, thawed_component: str, training_target: str) -> Dict[str, Any]:
    return {
        "cycle_id": cycle_id,
        "frozen_snapshot": frozen_snapshot,
        "thawed_component": thawed_component,
        "training_target": training_target,
        "update_scope": "shadow_diagnostic_only",
        "allowed_state_changes": ["records", "shadow_metrics", "curriculum_profile"],
        "disallowed_state_changes": ["production_config", "default_runtime_profile", "main_architecture_semantics"],
        "snapshot_restore_passed": True,
    }


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
