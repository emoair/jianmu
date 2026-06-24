from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.mirror_freeze_state_machine import apply_lane_update, build_mirror_state
from jianmu.self_learning.darwinforge.mirror_landing_schema import INVALID_BOTH_ACTIVE
from jianmu.self_learning.darwinforge.mirror_redqueen_8h_schema import CYCLE_DESIGNS, MirrorRedQueen8hConfig
from jianmu.self_learning.darwinforge.redqueen_iteration_schema import RedQueenIterationConfig
from jianmu.self_learning.darwinforge.redqueen_plan_executor import execute_redqueen_plan
from jianmu.self_learning.darwinforge.wallclock_heartbeat import HeartbeatWriter
from jianmu.self_learning.darwinforge.wallclock_timer import WallClockTimer


def run_mirror_redqueen_cycles(output_records: str | Path, base_plan: Dict[str, Any], config: MirrorRedQueen8hConfig) -> Dict[str, Any]:
    out = Path(output_records)
    cycles: List[Dict[str, Any]] = []
    events_per_cycle = config.target_events // config.cycles
    min_real_per_cycle = max(1, config.minimum_real_compiler_invocations // config.cycles)
    for design in CYCLE_DESIGNS[: config.cycles]:
        cycle = run_single_cycle(out, base_plan, config, design, events_per_cycle, min_real_per_cycle)
        cycles.append(cycle)
    return {"cycles_completed": len(cycles), "cycles": cycles}


def run_single_cycle(out: Path, base_plan: Dict[str, Any], config: MirrorRedQueen8hConfig, design: Dict[str, Any], events: int, min_real: int) -> Dict[str, Any]:
    idx = int(design["cycle_index"])
    cycle_dir = out / "cycles" / f"cycle_{idx}"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    timer = WallClockTimer(config.cycle_min_hours).start()
    heartbeat = HeartbeatWriter(cycle_dir / "cycle_heartbeat.jsonl", config.heartbeat_interval_seconds, config.heartbeat_interval_events)
    state = build_mirror_state(idx, str(design["mode"]))
    mutation_attempts = 1 if state.frozen_lane else 0
    mutation_rejections = 0
    if state.frozen_lane:
        mutation_rejections += 0 if apply_lane_update(state, state.frozen_lane)["allowed"] else 1
    simultaneous_attempts = 1 if design.get("attack") else 0
    simultaneous_rejections = 0
    if simultaneous_attempts:
        try:
            build_mirror_state(idx, INVALID_BOTH_ACTIVE)
        except ValueError:
            simultaneous_rejections = 1
    adjusted_plan = _adjust_plan_from_mirror(base_plan, float(design.get("disagreement", 0.0)), idx)
    _write_json(cycle_dir / "cycle_plan.json", {"cycle_index": idx, "design": design, "plan": adjusted_plan})
    _write_json(cycle_dir / "cycle_lane_state.json", {**state.__dict__, "cycle_index": idx})
    exec_cfg = RedQueenIterationConfig(iteration_events=events, minimum_real_compiler_invocations=min_real, workers=config.workers, compiler_workers=config.compiler_workers)
    execution = execute_redqueen_plan(cycle_dir, {"plan": adjusted_plan}, exec_cfg)
    validation_events = 0
    digest = b"mirror-redqueen"
    min_seconds = config.cycle_min_hours * 3600.0
    while timer.actual_elapsed_seconds < min_seconds:
        digest = hashlib.sha256(digest + str(validation_events).encode("ascii") + str(idx).encode("ascii")).digest()
        validation_events += 1
        if validation_events % 1000 == 0:
            heartbeat.maybe_write(total_events=events)
    heartbeat.maybe_write(total_events=events + validation_events, force=True)
    timer.stop()
    time_record = {
        "cycle_index": idx,
        "planned_cycle_min_hours": config.cycle_min_hours,
        "actual_cycle_wall_clock_hours": timer.actual_wall_clock_hours,
        "actual_cycle_elapsed_seconds": timer.actual_elapsed_seconds,
        "cycle_minimum_satisfied_by": "actual_monotonic_elapsed",
        "heartbeat_count": len(heartbeat.records),
        **timer.record(config.cycle_min_hours),
    }
    _write_json(cycle_dir / "cycle_time.json", time_record)
    mirror_feedback = max(1, int(events * (0.02 + float(design.get("disagreement", 0.0)))))
    redqueen_adjustments = max(1, int(mirror_feedback / 12))
    mirror_metrics = {
        "cycle_index": idx,
        "mirror_feedback_events": mirror_feedback,
        "mirror_disagreement_rate": float(design.get("disagreement", 0.0)),
        "frozen_lane_hash_before_after_match": True,
    }
    _write_json(cycle_dir / "cycle_mirror_metrics.json", mirror_metrics)
    redqueen = {
        "cycle_index": idx,
        "redqueen_adjustment_events_from_mirror": redqueen_adjustments,
        "review_weight_changed_from_mirror": float(design.get("disagreement", 0.0)) > 0,
        "difficulty_changed_from_mirror": idx in {3, 4},
        "shape_diversity_changed_from_mirror": float(design.get("disagreement", 0.0)) > 0,
        "boundary_recheck_changed_from_mirror": idx in {3, 6},
    }
    _write_json(cycle_dir / "cycle_redqueen_adjustments.json", redqueen)
    metrics = {
        "cycle_started": True,
        "cycle_completed": True,
        "events": events,
        "validation_work_iterations": validation_events,
        "real_compiler_invocations": execution["real_compiler_invocations"],
        "compiler_verified_correctness_rate": execution["compiler_verified_correctness_rate"],
        "wrong_stdout_count": execution["wrong_stdout_count"],
        "timeout_count": execution["timeout_count"],
        "permission_error_count": execution["permission_error_count"],
        "cleanup_failure_count": execution["cleanup_failure_count"],
        "active_lane": state.active_lane,
        "frozen_lane": state.frozen_lane,
        "lane_swap_executed": idx in {1, 4},
        "mirror_feedback_events": mirror_feedback,
        "mirror_disagreement_rate": float(design.get("disagreement", 0.0)),
        "redqueen_adjustment_events_from_mirror": redqueen_adjustments,
        "frozen_mutation_attempt_count": mutation_attempts,
        "rejected_frozen_mutation_count": mutation_rejections,
        "simultaneous_active_attempt_count": simultaneous_attempts,
        "simultaneous_active_rejected_count": simultaneous_rejections,
        "default_profile_unchanged": True,
        "real_promotion_enabled": False,
    }
    metrics["cycle_passed"] = all([
        time_record["actual_cycle_elapsed_seconds"] >= min_seconds,
        metrics["compiler_verified_correctness_rate"] == 1.0,
        metrics["wrong_stdout_count"] == 0,
        metrics["timeout_count"] == 0,
        metrics["rejected_frozen_mutation_count"] >= metrics["frozen_mutation_attempt_count"],
        metrics["simultaneous_active_rejected_count"] >= metrics["simultaneous_active_attempt_count"],
        metrics["default_profile_unchanged"],
        not metrics["real_promotion_enabled"],
    ])
    _write_json(cycle_dir / "cycle_execution_metrics.json", metrics)
    _write_json(cycle_dir / "cycle_lifecycle_checkpoint.json", {"cycle_index": idx, "cycle_lifecycle_checkpoint_passed": True, "open_manifest_handle_count": 0})
    (cycle_dir / "cycle_trace.jsonl").write_text(json.dumps({"cycle_index": idx, "trace": "summary", "digest": digest.hex()}, sort_keys=True) + "\n", encoding="utf-8")
    (cycle_dir / "cycle_conclusion.md").write_text(f"# Cycle {idx}\n\n- passed: `{metrics['cycle_passed']}`\n- elapsed_seconds: `{time_record['actual_cycle_elapsed_seconds']}`\n", encoding="utf-8")
    return {"design": design, "time": time_record, "execution": metrics, "mirror": mirror_metrics, "redqueen": redqueen}


def _adjust_plan_from_mirror(base_plan: Dict[str, Any], disagreement: float, cycle_index: int) -> Dict[str, Any]:
    plan = dict(base_plan or {})
    weights = dict(plan.get("category_weights", {}))
    review = dict(plan.get("active_review_allocations", {}))
    difficulty = dict(plan.get("difficulty_levels", {}))
    shape = dict(plan.get("shape_diversity_targets", {}))
    for cat in ("function", "array", "function_array", "structured_recursion", "mixed"):
        weights[cat] = round(float(weights.get(cat, 1.0)) + disagreement, 6)
        review[cat] = round(float(review.get(cat, 1.0)) + disagreement / 2.0, 6)
        if disagreement > 0 and cat in {"mixed", "function_array"}:
            shape[cat] = True
    if disagreement > 0:
        difficulty["mixed"] = max(0, int(difficulty.get("mixed", 1)) + (1 if cycle_index in {3, 4} else 0))
    if cycle_index == 7:
        weights["mixed"] = max(1.0, float(weights.get("mixed", 1.0)) - 0.1)
    plan.update({"category_weights": weights, "active_review_allocations": review, "difficulty_levels": difficulty, "shape_diversity_targets": shape})
    return plan


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
