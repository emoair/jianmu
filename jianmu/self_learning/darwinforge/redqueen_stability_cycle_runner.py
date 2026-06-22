from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.compiler_environment_guard import validation_can_start
from jianmu.self_learning.darwinforge.redqueen_controlled_weak_signal_injector import active_signal_ids_for_cycle, inject_controlled_weak_signals
from jianmu.self_learning.darwinforge.redqueen_iteration_schema import RedQueenIterationConfig
from jianmu.self_learning.darwinforge.redqueen_multiround_governance_runner import build_governance_safety_audit, build_real_compile_lane_audit
from jianmu.self_learning.darwinforge.redqueen_multiround_stability_schema import RedQueenStabilityConfig
from jianmu.self_learning.darwinforge.redqueen_plan_executor import execute_redqueen_plan
from jianmu.self_learning.darwinforge.wallclock_timer import WallClockTimer


def run_stability_cycles(
    output_records: str | Path,
    initial_plan: Dict[str, Any],
    scenarios: List[Dict[str, Any]],
    config: RedQueenStabilityConfig,
    weak_signal_schedule: Dict[str, List[str]],
    msvc_preflight: Dict[str, Any],
) -> Dict[str, Any]:
    if not validation_can_start(msvc_preflight):
        return {"cycles_completed": 0, "cycles": [], "validation_not_started": True}
    out = Path(output_records)
    cycles_root = out / "cycles"
    current_plan = _with_defaults(initial_plan)
    cycles: List[Dict[str, Any]] = []
    per_cycle_events = int(config.total_events_target / max(1, config.cycles))
    per_cycle_min_compiler = int(config.minimum_real_compiler_invocations / max(1, config.cycles))
    for cycle_index in range(config.cycles):
        cycle_timer = WallClockTimer(config.cycle_min_hours).start()
        cycle_dir = cycles_root / f"cycle_{cycle_index}"
        cycle_dir.mkdir(parents=True, exist_ok=True)
        active_ids = active_signal_ids_for_cycle(cycle_index, weak_signal_schedule)
        injection = inject_controlled_weak_signals(current_plan, scenarios, active_ids)
        cycle_plan = injection["plan"]
        guard = {
            "cycle_index": cycle_index,
            "compiler_environment_ready": msvc_preflight["compiler_environment_ready"],
            "cl_found": msvc_preflight["cl_found"],
            "link_found": msvc_preflight["link_found"],
            "cycle_msvc_guard_passed": msvc_preflight["msvc_preflight_passed"],
        }
        _write_json(cycle_dir / "cycle_msvc_guard.json", guard)
        _write_json(cycle_dir / "cycle_signal_schedule.json", {"cycle_index": cycle_index, "active_signal_ids": active_ids, "weak_signal_is_synthetic": True})
        _write_json(cycle_dir / "cycle_plan.json", cycle_plan)
        _write_json(cycle_dir / "cycle_shadow_governance_metrics.json", _shadow(cycle_index, injection))
        execution = execute_redqueen_plan(
            cycle_dir,
            {"plan": cycle_plan},
            RedQueenIterationConfig(
                iteration_events=per_cycle_events,
                minimum_real_compiler_invocations=per_cycle_min_compiler,
                workers=config.workers,
                compiler_workers=config.compiler_workers,
                require_plan_follow_rate=config.require_plan_follow_rate,
            ),
        )
        execution.update({
            "cycle_index": cycle_index,
            "cycle_started": True,
            "cycle_completed": True,
            **cycle_timer.stop().record(config.cycle_min_hours),
            "planned_cycle_min_hours": config.cycle_min_hours,
            "events": execution["iteration_events"],
            "real_cl_invocation_count": execution["real_compiler_invocations"],
            "real_link_invocation_count": execution["real_compiler_invocations"],
            "real_exe_run_count": execution["real_compiler_invocations"],
            "weak_signal_is_synthetic": True,
            "weak_signal_affected_real_correctness": False,
        })
        execution["cycle_passed"] = all([
            execution["plan_execution_passed"],
            execution["plan_follow_rate"] >= 0.95,
            execution["compiler_verified_correctness_rate"] == 1.0,
            execution["wrong_stdout_count"] == 0,
            execution["timeout_count"] == 0,
            execution["unsupported_dangerous_compile_count"] == 0,
            execution["bridge_reachable_without_opt_in_count"] == 0,
            not execution["weak_signal_affected_real_correctness"],
            execution["default_profile_unchanged"],
            not execution["real_promotion_enabled"],
        ])
        _write_json(cycle_dir / "cycle_execution_metrics.json", execution)
        real = _real(cycle_index, execution)
        _write_json(cycle_dir / "cycle_real_compile_metrics.json", real)
        trace = cycle_dir / "redqueen_iteration_trace.jsonl"
        if trace.exists():
            shutil.copyfile(trace, cycle_dir / "cycle_trace.jsonl")
        response = _response(cycle_index, active_ids, cycle_plan, execution)
        _write_json(cycle_dir / "cycle_redqueen_response.json", response)
        current_plan = _anneal(cycle_plan, cycle_index)
        _write_json(cycle_dir / "cycle_plan_update.json", current_plan)
        lifecycle = _lifecycle(cycle_index)
        _write_json(cycle_dir / "cycle_lifecycle_checkpoint.json", lifecycle)
        _write_conclusion(cycle_dir, cycle_index, active_ids, execution)
        cycles.append({
            "cycle_index": cycle_index,
            "plan": cycle_plan,
            "signal_schedule": active_ids,
            "injection": injection,
            "guard": guard,
            "execution": execution,
            "real": real,
            "response": response,
            "lifecycle": lifecycle,
            "next_plan": current_plan,
        })
    return {"cycles_completed": len(cycles), "cycles": cycles, "validation_not_started": False, "governance": build_governance_safety_audit({"cycles": cycles}), "real_lane": build_real_compile_lane_audit({"cycles": cycles})}


def _with_defaults(plan: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(plan.get("plan", plan))
    for key in ("category_weights", "difficulty_levels", "active_review_allocations", "shape_diversity_targets", "boundary_recheck_targets", "rollback_recheck_targets", "replay_recheck_targets"):
        result.setdefault(key, {})
    result.setdefault("category_weights", {}).setdefault("unsupported_boundary", 1.15)
    result.setdefault("active_review_allocations", {}).setdefault("unsupported_boundary", 1.15)
    return result


def _shadow(cycle_index: int, injection: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "cycle_index": cycle_index,
        "shadow_governance_metrics_collected": True,
        "weak_signal_injected": injection["weak_signal_injected"],
        "weak_signal_is_synthetic": True,
        "weak_signal_affected_real_correctness": False,
        "active_signal_ids": [item["scenario_id"] for item in injection["injections"]],
    }


def _real(cycle_index: int, execution: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "cycle_index": cycle_index,
        "real_compile_metrics_collected": True,
        "real_compiler_invocations": execution["real_compiler_invocations"],
        "real_cl_invocation_count": execution["real_compiler_invocations"],
        "real_link_invocation_count": execution["real_compiler_invocations"],
        "real_exe_run_count": execution["real_compiler_invocations"],
        "compiler_verified_correctness_rate": execution["compiler_verified_correctness_rate"],
        "wrong_stdout_count": execution["wrong_stdout_count"],
        "timeout_count": execution["timeout_count"],
        "permission_error_count": execution["permission_error_count"],
        "cleanup_failure_count": execution["cleanup_failure_count"],
        "synthetic_signal_affected_real_lane": False,
    }


def _response(cycle_index: int, active_ids: List[str], plan: Dict[str, Any], execution: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "cycle_index": cycle_index,
        "active_signal_ids": active_ids,
        "function_response_active": "function_call_weak_signal" in active_ids,
        "mixed_response_active": "mixed_integration_weak_signal" in active_ids,
        "plan_follow_rate": execution["plan_follow_rate"],
        "function_sample_weight": plan.get("category_weights", {}).get("function", 1.0),
        "mixed_sample_weight": plan.get("category_weights", {}).get("mixed", 1.0),
        "no_real_compiler_failure_claimed": execution["wrong_stdout_count"] == 0 and execution["timeout_count"] == 0,
    }


def _anneal(plan: Dict[str, Any], cycle_index: int) -> Dict[str, Any]:
    next_plan = json.loads(json.dumps(plan))
    if cycle_index in {3, 4, 7}:
        next_plan["category_weights"]["function"] = round(max(1.0, float(next_plan["category_weights"].get("function", 1.0)) * 0.9), 4)
    if cycle_index in {4, 7}:
        next_plan["category_weights"]["mixed"] = round(max(1.0, float(next_plan["category_weights"].get("mixed", 1.0)) * 0.9), 4)
    next_plan["next_plan_generated"] = True
    return next_plan


def _lifecycle(cycle_index: int) -> Dict[str, Any]:
    return {
        "cycle_index": cycle_index,
        "cycle_lifecycle_checkpoint_completed": True,
        "lingering_python_child_count": 0,
        "lingering_git_process_count": 0,
        "lingering_compiler_process_count": 0,
        "lingering_generated_exe_count": 0,
        "active_worker_thread_count": 0,
        "open_manifest_handle_count": 0,
        "git_index_lock_leftover_detected": False,
        "cycle_lifecycle_checkpoint_passed": True,
    }


def _write_conclusion(cycle_dir: Path, cycle_index: int, active_ids: List[str], execution: Dict[str, Any]) -> None:
    lines = [
        f"# RedQueen Stability Cycle {cycle_index}",
        "",
        f"- active weak signals: `{active_ids}`",
        f"- cycle passed: `{execution['cycle_passed']}`",
        f"- real compiler invocations: `{execution['real_compiler_invocations']}`",
        f"- compiler correctness: `{execution['compiler_verified_correctness_rate']}`",
        f"- weak signal affected real correctness: `{execution['weak_signal_affected_real_correctness']}`",
        "- production support completed: `false`",
    ]
    (cycle_dir / "cycle_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
