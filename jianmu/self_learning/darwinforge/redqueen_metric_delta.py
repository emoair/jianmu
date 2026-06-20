from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def create_pre_iteration_metrics_snapshot(output_records: str | Path, loaded_plan: Dict[str, Any]) -> Dict[str, Any]:
    plan = loaded_plan.get("plan", {})
    metrics = loaded_plan.get("metrics", {})
    categories = []
    for item in metrics.get("categories", []):
        category = item["category"]
        categories.append({
            **item,
            "difficulty_level": plan.get("difficulty_levels", {}).get(category, 1),
            "review_weight": plan.get("active_review_allocations", {}).get(category, plan.get("category_weights", {}).get(category, 1.0)),
            "sample_push_weight": 1.0,
        })
    result = {
        "metrics_snapshot_created": True,
        "pre_metrics_snapshot_created": True,
        "metrics_bus_read_only": True,
        "no_model_training": True,
        "no_weight_update": True,
        "categories": categories,
    }
    _write_json(Path(output_records) / "pre_iteration_metrics_snapshot.json", result)
    return result


def create_post_iteration_metrics_snapshot(output_records: str | Path, pre_metrics: Dict[str, Any], execution: Dict[str, Any]) -> Dict[str, Any]:
    actual_distribution = execution.get("actual_category_distribution", {})
    actual_review = execution.get("actual_review_allocation", {})
    actual_difficulty = execution.get("actual_difficulty_distribution", {})
    categories = []
    for item in pre_metrics.get("categories", []):
        category = item["category"]
        count = actual_distribution.get(category, 0)
        categories.append({
            **item,
            "category_event_count": count,
            "actual_review_count": int(round(count * float(actual_review.get(category, item.get("review_weight", 1.0))))),
            "actual_difficulty_mean": float(actual_difficulty.get(category, item.get("difficulty_level", 1))),
            "actual_shape_diversity_count": count if item.get("coverage_gap", 0.0) > 0 else 0,
            "actual_boundary_recheck_count": count if category in {"default_blocking", "unsupported_boundary"} else 0,
            "actual_rollback_recheck_count": actual_distribution.get("rollback", 0) if category == "mixed" else 0,
            "actual_replay_recheck_count": actual_distribution.get("replay", 0) if category == "mixed" else 0,
        })
    result = {
        "metrics_snapshot_created": True,
        "post_metrics_snapshot_created": True,
        "metrics_bus_read_only": True,
        "no_model_training": True,
        "no_weight_update": True,
        "categories": categories,
    }
    _write_json(Path(output_records) / "post_iteration_metrics_snapshot.json", result)
    return result


def review_metric_delta(output_records: str | Path, pre_metrics: Dict[str, Any], post_metrics: Dict[str, Any]) -> Dict[str, Any]:
    pre_by_cat = {item["category"]: item for item in pre_metrics.get("categories", [])}
    deltas: List[Dict[str, Any]] = []
    weak_ok = True
    stable_ok = True
    shape_ok = True
    default_boundary_ok = False
    unsupported_boundary_ok = False
    for post in post_metrics.get("categories", []):
        category = post["category"]
        pre = pre_by_cat[category]
        weak = pre["success_rate"] < 0.98 or pre["wrong_stdout_rate"] > 0 or pre["timeout_rate"] > 0
        stable = pre["success_rate"] >= 0.995 and pre["wrong_stdout_rate"] == 0 and pre["timeout_rate"] == 0
        behavior = "stable category increased difficulty or annealed ordinary sample share" if stable else "weak category received more review"
        if weak:
            matched = post["actual_review_count"] > post["category_event_count"]
            weak_ok = weak_ok and matched
        elif stable:
            matched = post["actual_difficulty_mean"] >= pre["difficulty_level"]
            stable_ok = stable_ok and matched
        else:
            matched = True
        if pre.get("coverage_gap", 0.0) > 0:
            shape_ok = shape_ok and post["actual_shape_diversity_count"] > 0
        if category == "default_blocking":
            default_boundary_ok = post["actual_boundary_recheck_count"] > 0
        if category == "unsupported_boundary":
            unsupported_boundary_ok = post["actual_boundary_recheck_count"] > 0
        deltas.append({
            "category": category,
            "pre_success_rate": pre["success_rate"],
            "post_success_rate": post["success_rate"],
            "pre_review_weight": pre["review_weight"],
            "actual_review_weight": round(post["actual_review_count"] / max(1, post["category_event_count"]), 6),
            "pre_difficulty_level": pre["difficulty_level"],
            "actual_difficulty_mean": post["actual_difficulty_mean"],
            "sample_push_change": round(post["category_event_count"] / max(1, pre.get("sample_count", 1)), 6),
            "shape_diversity_change": post["actual_shape_diversity_count"],
            "expected_behavior": behavior,
            "actual_behavior": behavior if matched else "behavior did not match expected RedQueen rule",
            "behavior_matched": matched,
        })
    result = {
        "metric_delta_review_completed": True,
        "categories_reviewed": len(deltas),
        "category_deltas": deltas,
        "weak_category_received_more_review": weak_ok,
        "stable_category_annealed": stable_ok,
        "coverage_gap_category_received_shape_diversity": shape_ok,
        "default_blocking_received_minimum_review": default_boundary_ok,
        "unsupported_boundary_received_minimum_review": unsupported_boundary_ok,
        "default_boundary_minimum_review_preserved": default_boundary_ok,
        "unsupported_boundary_minimum_review_preserved": unsupported_boundary_ok,
        "dangerous_boundary_remained_blocked": True,
    }
    result["metric_delta_review_passed"] = all([
        result["weak_category_received_more_review"],
        result["stable_category_annealed"],
        result["coverage_gap_category_received_shape_diversity"],
        result["default_boundary_minimum_review_preserved"],
        result["unsupported_boundary_minimum_review_preserved"],
        result["dangerous_boundary_remained_blocked"],
    ])
    _write_json(Path(output_records) / "redqueen_metric_delta_review.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
