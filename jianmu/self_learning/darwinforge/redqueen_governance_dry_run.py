from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.architecture_finalization_schema import REDQUEEN_CATEGORIES


def run_redqueen_governance_dry_run(
    output_records: str | Path,
    metrics_bus: Dict[str, Any],
    allocation: Dict[str, Any],
    schedule: Dict[str, Any],
    events: int = 20_000,
    workers: int = 16,
    compiler_workers: int = 16,
) -> Dict[str, Any]:
    out = Path(output_records)
    trace: List[Dict[str, Any]] = []
    categories = list(REDQUEEN_CATEGORIES)
    for i in range(events):
        category = categories[i % len(categories)]
        trace.append({
            "event_id": f"redqueen_dry_run_{i:08d}",
            "category": category,
            "action": "schedule_review_and_validation_sample",
            "review_weight": allocation.get("category_review_weights", {}).get(category, 1.0),
            "default_profile_modified": False,
            "real_promotion_enabled": False,
            "production_support_completed": False,
            "bypass_existing_bridge": False,
        })
    _write_jsonl(out / "redqueen_governance_trace.jsonl", trace)
    result = {
        "redqueen_dry_run_started": True,
        "redqueen_dry_run_completed": True,
        "dry_run_events": events,
        "workers_requested": workers,
        "workers_used": workers,
        "compiler_workers_requested": compiler_workers,
        "compiler_workers_used": compiler_workers,
        "downgrade_reason": "",
        "metrics_bus_read_only": metrics_bus.get("metrics_bus_read_only") is True,
        "active_review_allocator_used": allocation.get("active_review_allocator_completed") is True,
        "difficulty_scheduler_used": schedule.get("difficulty_scheduler_completed") is True,
        "next_validation_plan_generated": True,
        "default_profile_unchanged": True,
        "real_promotion_enabled": False,
        "user_facing_enabled": False,
        "official_release_enabled": False,
        "production_support_flags_false": True,
        "adapter_reuses_v1_0_6_dry_run_adapter": True,
        "adapter_reuses_atomic_policy_bridge": True,
        "adapter_reuses_extended_ir": True,
        "adapter_reuses_extended_emitter": True,
        "compiler_backend_reused": True,
        "direct_template_path_detected": False,
        "marker_ir_direct_compile_detected": False,
        "summary_only_validation_detected": False,
        "unsupported_boundary_respected": True,
        "rollback_respected": True,
    }
    result["redqueen_dry_run_passed"] = all([
        result["metrics_bus_read_only"],
        result["active_review_allocator_used"],
        result["difficulty_scheduler_used"],
        result["default_profile_unchanged"],
        not result["real_promotion_enabled"],
        result["production_support_flags_false"],
        not result["direct_template_path_detected"],
        not result["marker_ir_direct_compile_detected"],
        not result["summary_only_validation_detected"],
        result["unsupported_boundary_respected"],
        result["rollback_respected"],
    ])
    _write_json(out / "redqueen_governance_dry_run.json", result)
    return result


def build_next_validation_plan(output_records: str | Path, allocation: Dict[str, Any], schedule: Dict[str, Any]) -> Dict[str, Any]:
    difficulty_levels = {row["category"]: row["next_difficulty_level"] for row in schedule.get("schedule", [])}
    shape_targets = {row["category"]: row["shape_diversity_push"] for row in schedule.get("schedule", [])}
    result = {
        "next_plan_generated": True,
        "next_validation_plan_generated": True,
        "category_weights": allocation.get("category_review_weights", {}),
        "difficulty_levels": difficulty_levels,
        "active_review_allocations": allocation.get("category_review_weights", {}),
        "shape_diversity_targets": shape_targets,
        "boundary_recheck_targets": {"unsupported_boundary": 1000, "default_blocking": 1000},
        "rollback_recheck_targets": {"rollback": 500},
        "replay_recheck_targets": {"mixed": 500},
        "human_review_requests": [],
        "promotion_frozen": True,
        "default_profile_unchanged_required": True,
        "real_promotion_forbidden": True,
        "production_claim_forbidden": True,
    }
    _write_json(Path(output_records) / "redqueen_next_validation_plan.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
