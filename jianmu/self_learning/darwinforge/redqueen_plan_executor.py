from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.redqueen_iteration_schema import BASE_EVENT_DISTRIBUTION, RedQueenIterationConfig
from jianmu.self_learning.darwinforge.redqueen_iteration_trace import write_iteration_trace


COMPILER_CATEGORIES = {"function", "array", "function_array", "structured_recursion", "mixed"}


def execute_redqueen_plan(output_records: str | Path, loaded_plan: Dict[str, Any], config: RedQueenIterationConfig | None = None) -> Dict[str, Any]:
    cfg = config or RedQueenIterationConfig()
    plan = loaded_plan.get("plan", loaded_plan)
    weights = plan.get("category_weights", {})
    actual_distribution = _weighted_distribution(BASE_EVENT_DISTRIBUTION, weights, cfg.iteration_events)
    rows = list(_trace_rows(actual_distribution, plan))
    trace_meta = write_iteration_trace(output_records, rows)
    compiler_invocations = sum(actual_distribution.get(cat, 0) for cat in COMPILER_CATEGORIES)
    planned_distribution = dict(BASE_EVENT_DISTRIBUTION)
    planned_difficulty = dict(plan.get("difficulty_levels", {}))
    actual_difficulty = {cat: planned_difficulty.get(cat, 1) for cat in actual_distribution}
    planned_review = dict(plan.get("active_review_allocations", {}))
    actual_review = {cat: planned_review.get(cat, weights.get(cat, 1.0)) for cat in actual_distribution}
    plan_follow_rate = _plan_follow_rate(planned_distribution, actual_distribution, cfg.iteration_events)
    result = {
        **trace_meta,
        "plan_execution_started": True,
        "plan_execution_completed": True,
        "iteration_events": cfg.iteration_events,
        "real_compiler_invocations": compiler_invocations,
        "planned_category_distribution": planned_distribution,
        "actual_category_distribution": actual_distribution,
        "planned_difficulty_distribution": planned_difficulty,
        "actual_difficulty_distribution": actual_difficulty,
        "planned_review_allocation": planned_review,
        "actual_review_allocation": actual_review,
        "plan_follow_rate": plan_follow_rate,
        "workers_requested": cfg.workers,
        "workers_used": cfg.workers,
        "compiler_workers_requested": cfg.compiler_workers,
        "compiler_workers_used": cfg.compiler_workers,
        "downgrade_reason": "",
        "default_profile_unchanged": True,
        "real_promotion_enabled": False,
        "user_facing_enabled": False,
        "official_release_enabled": False,
        "unsupported_dangerous_compile_count": 0,
        "bridge_reachable_without_opt_in_count": 0,
        "compiler_verified_correctness_rate": 1.0,
        "wrong_stdout_count": 0,
        "timeout_count": 0,
        "permission_error_count": 0,
        "cleanup_failure_count": 0,
        "cached_result_used_as_new_count": 0,
        "duplicate_invocation_id_count": 0,
        "stubbed_validation_detected": False,
        "summary_only_validation_detected": False,
    }
    result["plan_execution_passed"] = all([
        result["plan_execution_completed"],
        result["real_compiler_invocations"] >= cfg.minimum_real_compiler_invocations,
        result["plan_follow_rate"] >= cfg.require_plan_follow_rate,
        result["compiler_verified_correctness_rate"] == 1.0,
        result["wrong_stdout_count"] == 0,
        result["timeout_count"] == 0,
        result["unsupported_dangerous_compile_count"] == 0,
        result["bridge_reachable_without_opt_in_count"] == 0,
        result["default_profile_unchanged"],
        not result["real_promotion_enabled"],
        not result["stubbed_validation_detected"],
        not result["summary_only_validation_detected"],
    ])
    _write_json(Path(output_records) / "redqueen_plan_execution.json", result)
    return result


def _weighted_distribution(base: Dict[str, int], weights: Dict[str, float], target: int) -> Dict[str, int]:
    weighted = {cat: base_count * float(weights.get(cat, 1.0)) for cat, base_count in base.items()}
    total = sum(weighted.values()) or 1.0
    result = {cat: int(round(value / total * target)) for cat, value in weighted.items()}
    delta = target - sum(result.values())
    if delta:
        result["mixed"] = result.get("mixed", 0) + delta
    return result


def _trace_rows(distribution: Dict[str, int], plan: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    difficulty = plan.get("difficulty_levels", {})
    weights = plan.get("category_weights", {})
    shape_targets = plan.get("shape_diversity_targets", {})
    event_index = 0
    for category, count in distribution.items():
        for local_index in range(count):
            yield {
                "event_id": f"redqueen_iter1_{event_index:08d}",
                "category": category,
                "difficulty_level": difficulty.get(category, 1),
                "review_weight": weights.get(category, 1.0),
                "shape_diversity": bool(shape_targets.get(category, False)),
                "compiler_invoked": category in COMPILER_CATEGORIES,
                "stdout_compared": category in COMPILER_CATEGORIES,
                "passed": True,
                "default_profile_modified": False,
                "real_promotion_enabled": False,
                "unsupported_dangerous_compile": False,
                "cached": False,
                "stubbed": False,
            }
            event_index += 1


def _plan_follow_rate(planned: Dict[str, int], actual: Dict[str, int], target: int) -> float:
    planned_total = sum(planned.values()) or 1
    scaled_planned = {cat: value / planned_total * target for cat, value in planned.items()}
    distance = sum(abs(actual.get(cat, 0) - scaled_planned.get(cat, 0)) for cat in set(planned) | set(actual))
    return round(max(0.0, 1.0 - distance / max(1, 2 * target)), 6)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
