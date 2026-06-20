from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


REQUIRED_PLAN_KEYS = (
    "category_weights",
    "difficulty_levels",
    "active_review_allocations",
    "shape_diversity_targets",
    "boundary_recheck_targets",
    "rollback_recheck_targets",
    "replay_recheck_targets",
)


def load_redqueen_iteration_plan(source_records_v1_0_8_2: str | Path, output_records: str | Path) -> Dict[str, Any]:
    source = Path(source_records_v1_0_8_2)
    paths = {
        "next_plan": source / "redqueen_next_validation_plan.json",
        "metrics": source / "redqueen_metrics_snapshot.json",
        "allocation": source / "redqueen_active_review_allocation.json",
        "difficulty_schedule": source / "redqueen_difficulty_schedule.json",
        "governance_policy": source / "redqueen_self_governance_policy.json",
    }
    loaded = {name: _load(path) for name, path in paths.items()}
    plan = loaded["next_plan"]
    missing_keys = [key for key in REQUIRED_PLAN_KEYS if key not in plan]
    result = {
        "plan_loader_completed": True,
        "source_next_plan_found": paths["next_plan"].exists(),
        "source_metrics_found": paths["metrics"].exists(),
        "source_allocation_found": paths["allocation"].exists(),
        "source_difficulty_schedule_found": paths["difficulty_schedule"].exists(),
        "source_governance_policy_found": paths["governance_policy"].exists(),
        "source_plan_loaded": False,
        "promotion_frozen": plan.get("promotion_frozen") is True,
        "default_profile_unchanged_required": plan.get("default_profile_unchanged_required") is True,
        "real_promotion_forbidden": plan.get("real_promotion_forbidden") is True,
        "production_claim_forbidden": plan.get("production_claim_forbidden") is True,
        "missing_plan_keys": missing_keys,
        "plan": plan,
        "metrics": loaded["metrics"],
        "allocation": loaded["allocation"],
        "difficulty_schedule": loaded["difficulty_schedule"],
        "governance_policy": loaded["governance_policy"],
    }
    result["source_plan_loaded"] = all([
        result["source_next_plan_found"],
        result["source_metrics_found"],
        result["source_allocation_found"],
        result["source_difficulty_schedule_found"],
        result["source_governance_policy_found"],
        plan.get("next_plan_generated") is True,
        not missing_keys,
    ])
    result["plan_loader_passed"] = all([
        result["source_plan_loaded"],
        result["promotion_frozen"],
        result["default_profile_unchanged_required"],
        result["real_promotion_forbidden"],
        result["production_claim_forbidden"],
    ])
    _write_json(Path(output_records) / "redqueen_plan_loader.json", _public(result))
    return result


def _load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _public(result: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in result.items() if k not in {"plan", "metrics", "allocation", "difficulty_schedule", "governance_policy"}}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
