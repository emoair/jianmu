from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


ALLOWED_ACTIONS = (
    "increase_review_weight",
    "decrease_review_weight",
    "increase_difficulty",
    "decrease_difficulty",
    "increase_sample_push",
    "decrease_sample_push",
    "request_human_review",
    "require_boundary_recheck",
    "require_replay_recheck",
    "require_rollback_recheck",
    "freeze_promotion",
    "reject_unsupported",
    "keep_default_profile_unchanged",
)

FORBIDDEN_ACTIONS = (
    "enable_real_promotion",
    "modify_default_profile",
    "mark_production_completed",
    "enable_user_facing_release",
    "call_external_api",
    "train_model_weights",
    "bypass_atomic_policy",
    "bypass_extended_ir",
    "bypass_extended_emitter",
    "compile_unsupported_dangerous_input",
)


def build_self_governance_policy(output_records: str | Path) -> Dict[str, Any]:
    result = {
        "governance_policy_generated": True,
        "allowed_actions": list(ALLOWED_ACTIONS),
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "production_promotion_forbidden": True,
        "default_profile_modification_forbidden": True,
        "external_api_forbidden": True,
        "model_training_forbidden": True,
        "bypass_forbidden": True,
        "self_governance_policy_passed": True,
    }
    _write_json(Path(output_records) / "redqueen_self_governance_policy.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
