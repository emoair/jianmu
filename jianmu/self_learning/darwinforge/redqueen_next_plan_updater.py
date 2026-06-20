from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def update_redqueen_next_plan(output_records: str | Path, loaded_plan: Dict[str, Any], delta: Dict[str, Any]) -> Dict[str, Any]:
    plan = loaded_plan.get("plan", loaded_plan)
    result = {
        "next_plan_v2_generated": True,
        "source_iteration": "v1.0.8.3",
        "category_weights": dict(plan.get("category_weights", {})),
        "difficulty_levels": dict(plan.get("difficulty_levels", {})),
        "active_review_allocations": dict(plan.get("active_review_allocations", {})),
        "sample_push_weights": {
            item["category"]: max(0.25, 1.0 + float(item.get("sample_push_change", 0.0)) * 0.01)
            for item in delta.get("category_deltas", [])
        },
        "shape_diversity_targets": dict(plan.get("shape_diversity_targets", {})),
        "boundary_recheck_targets": dict(plan.get("boundary_recheck_targets", {})),
        "rollback_recheck_targets": dict(plan.get("rollback_recheck_targets", {})),
        "replay_recheck_targets": dict(plan.get("replay_recheck_targets", {})),
        "human_review_requests": [],
        "promotion_frozen": True,
        "default_profile_unchanged_required": True,
        "real_promotion_forbidden": True,
        "production_claim_forbidden": True,
    }
    _write_json(Path(output_records) / "redqueen_next_validation_plan_v2.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
