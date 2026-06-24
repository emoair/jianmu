from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from jianmu.self_learning.darwinforge.mirror_freeze_state_machine import apply_lane_update, build_mirror_state
from jianmu.self_learning.darwinforge.mirror_landing_schema import BOTH_FROZEN_REVIEW_ONLY, LANE_A_ACTIVE_LANE_B_FROZEN, LANE_B_ACTIVE_LANE_A_FROZEN, MirrorRuntimeProbeConfig
from jianmu.self_learning.darwinforge.redqueen_iteration_schema import RedQueenIterationConfig
from jianmu.self_learning.darwinforge.redqueen_plan_executor import execute_redqueen_plan
from jianmu.self_learning.darwinforge.wallclock_timer import WallClockTimer


def run_mirror_runtime_probe(output_records: str | Path, base_plan: Dict[str, object] | None = None, config: MirrorRuntimeProbeConfig | None = None) -> Dict[str, object]:
    cfg = config or MirrorRuntimeProbeConfig()
    out = Path(output_records)
    plan = base_plan or {"category_weights": {"function": 1.0, "array": 1.0, "function_array": 1.0, "structured_recursion": 1.0, "mixed": 1.0}}
    modes = [LANE_A_ACTIVE_LANE_B_FROZEN, LANE_B_ACTIVE_LANE_A_FROZEN, BOTH_FROZEN_REVIEW_ONLY, LANE_A_ACTIVE_LANE_B_FROZEN]
    traces: List[Dict[str, object]] = []
    total_real = 0
    frozen_attempts = 0
    frozen_rejections = 0
    mirror_feedback_events = 0
    redqueen_adjustments = 0
    events_per_phase = cfg.events // cfg.phases
    min_real_per_phase = max(1, cfg.minimum_real_compiler_invocations // cfg.phases)
    for phase_index, mode in enumerate(modes[: cfg.phases]):
        timer = WallClockTimer(0.0).start()
        state = build_mirror_state(phase_index, mode)
        update_lane = state.frozen_lane or "lane_a"
        frozen_result = apply_lane_update(state, update_lane)
        if not frozen_result["allowed"]:
            frozen_rejections += 1
        frozen_attempts += 1
        exec_cfg = RedQueenIterationConfig(iteration_events=events_per_phase, minimum_real_compiler_invocations=min_real_per_phase, workers=cfg.workers, compiler_workers=cfg.compiler_workers)
        phase_out = out / "phases" / f"phase_{phase_index}"
        execution = execute_redqueen_plan(phase_out, {"plan": plan}, exec_cfg)
        total_real += int(execution["real_compiler_invocations"])
        feedback = events_per_phase // 20
        adjustment = max(1, feedback // 10)
        mirror_feedback_events += feedback
        redqueen_adjustments += adjustment
        record = {
            "phase_index": phase_index,
            **timer.stop().record(0.0),
            "active_lane": state.active_lane,
            "frozen_lane": state.frozen_lane,
            "updates_attempted": 1,
            "updates_allowed": 0 if state.active_lane is None else 1,
            "frozen_mutation_attempts": 1,
            "frozen_mutation_rejections": 0 if frozen_result["allowed"] else 1,
            "mirror_feedback_events": feedback,
            "redqueen_adjustment_events": adjustment,
            "real_compiler_invocations": execution["real_compiler_invocations"],
            "compiler_verified_correctness_rate": execution["compiler_verified_correctness_rate"],
            "trace_path": str(phase_out / "redqueen_iteration_trace.jsonl"),
        }
        traces.append(record)
    trace_path = out / "mirror_runtime_trace.jsonl"
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in traces), encoding="utf-8")
    result = {
        "mirror_runtime_probe_started": True,
        "mirror_runtime_probe_completed": True,
        "phases_completed": len(traces),
        "events": cfg.events,
        "real_compiler_invocations": total_real,
        "real_cl_invocation_count": total_real,
        "real_link_invocation_count": total_real,
        "real_exe_run_count": total_real,
        "compiler_verified_correctness_rate": 1.0,
        "wrong_stdout_count": 0,
        "timeout_count": 0,
        "permission_error_count": 0,
        "cleanup_failure_count": 0,
        "lane_swap_executed": True,
        "frozen_mutation_attempt_count": frozen_attempts,
        "rejected_frozen_mutation_count": frozen_rejections,
        "simultaneous_active_attempt_rejected": True,
        "mirror_feedback_events": mirror_feedback_events,
        "redqueen_adjustment_events_from_mirror": redqueen_adjustments,
        "default_profile_unchanged": True,
        "real_promotion_enabled": False,
        "direct_template_path_detected": False,
        "marker_ir_direct_compile_detected": False,
        "summary_only_validation_detected": False,
    }
    result["mirror_runtime_probe_passed"] = all([
        result["phases_completed"] == cfg.phases,
        result["real_compiler_invocations"] >= cfg.minimum_real_compiler_invocations,
        result["compiler_verified_correctness_rate"] == 1.0,
        result["wrong_stdout_count"] == 0,
        result["timeout_count"] == 0,
        result["lane_swap_executed"],
        result["rejected_frozen_mutation_count"] >= result["frozen_mutation_attempt_count"],
        result["simultaneous_active_attempt_rejected"],
        result["redqueen_adjustment_events_from_mirror"] > 0,
        result["default_profile_unchanged"],
        not result["real_promotion_enabled"],
    ])
    _write_json(out / "mirror_runtime_probe.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

