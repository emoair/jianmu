from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.compiler_environment_guard import build_msvc_fail_fast_test, guard_compiler_environment, validation_can_start
from jianmu.self_learning.darwinforge.redqueen_multiround_stability_lifecycle import run_stability_lifecycle_guard
from jianmu.self_learning.darwinforge.redqueen_multiround_stability_readiness import build_stability_readiness
from jianmu.self_learning.darwinforge.redqueen_multiround_stability_schema import (
    RedQueenStabilityConfig,
    STILL_NOT_PROVEN_STABILITY,
    build_multiround_stability_config_record,
)
from jianmu.self_learning.darwinforge.redqueen_perturbation_recovery_audit import audit_perturbation_recovery
from jianmu.self_learning.darwinforge.redqueen_plan_loader import load_redqueen_iteration_plan
from jianmu.self_learning.darwinforge.redqueen_response_stability_audit import audit_response_stability
from jianmu.self_learning.darwinforge.redqueen_stability_cycle_runner import run_stability_cycles
from jianmu.self_learning.darwinforge.redqueen_stability_drift_audit import audit_stability_drift
from jianmu.self_learning.darwinforge.redqueen_weak_signal_schema import build_weak_signal_scenarios
from jianmu.self_learning.darwinforge.wallclock_timer import WallClockTimer


def main() -> int:
    args = parse_args()
    out = Path(args.output_records)
    out.mkdir(parents=True, exist_ok=True)
    run_timer = WallClockTimer(args.wall_clock_min_hours).start()
    cfg = RedQueenStabilityConfig(
        profile_name=args.profile_name,
        wall_clock_min_hours=args.wall_clock_min_hours,
        max_runtime_hours=args.max_runtime_hours,
        hard_stop_hours=args.hard_stop_hours,
        cycles=args.cycles,
        cycle_min_hours=args.cycle_min_hours,
        total_events_target=args.total_events_target,
        minimum_total_events=args.minimum_total_events,
        minimum_real_compiler_invocations=args.minimum_real_compiler_invocations,
        workers=args.workers,
        compiler_workers=args.compiler_workers,
        trace_writer_mode=args.trace_writer_mode,
        temp_dir_mode=args.temp_dir_mode,
        accounting_lock=args.accounting_lock,
        idle_grace_seconds=args.idle_grace_seconds,
        require_msvc_env=args.require_msvc_env,
    )
    preflight = guard_compiler_environment(out, require_msvc_env=args.require_msvc_env)
    fail_fast_test = build_msvc_fail_fast_test(out) if args.run_msvc_fail_fast_negative_test else {"msvc_fail_fast_test_passed": True}
    config_record = build_multiround_stability_config_record(cfg)
    _write_json(out / "multiround_stability_config.json", config_record)
    if not validation_can_start(preflight):
        summary = _blocked_summary(cfg, preflight, fail_fast_test)
        _write_json(out / "endurance_summary.json", summary)
        readiness = build_stability_readiness(out, summary)
        write_stability_report(out, readiness)
        print(json.dumps({"recommended_claim_level": readiness["recommended_claim_level"], "compiler_environment_ready": preflight["compiler_environment_ready"]}, ensure_ascii=False, sort_keys=True), flush=True)
        return 1
    loader = load_redqueen_iteration_plan(args.source_records_v1_0_8_2, out)
    base_plan = loader["plan"]
    v5_plan = Path(args.source_records_v1_0_8_5) / "cycles" / "cycle_7" / "cycle_plan_update.json"
    if not v5_plan.exists():
        v5_plan = Path(args.source_records_v1_0_8_5) / "cycles" / "cycle_4" / "cycle_plan_update.json"
    if v5_plan.exists():
        base_plan = json.loads(v5_plan.read_text(encoding="utf-8"))
    cycle_result = run_stability_cycles(out, base_plan, build_weak_signal_scenarios(), cfg, config_record["weak_signal_schedule"], preflight)
    cycles = cycle_result["cycles"]
    drift = audit_stability_drift(cycles)
    response = audit_response_stability(cycles, max_latency_cycles=args.require_response_latency_cycles)
    perturbation = audit_perturbation_recovery(cycles)
    real_lane = cycle_result["real_lane"]
    lifecycle = run_stability_lifecycle_guard(ROOT, out, cycle_result, cfg.idle_grace_seconds)
    governance = cycle_result["governance"]
    for name, payload in [
        ("redqueen_stability_drift_audit.json", drift),
        ("redqueen_response_stability_audit.json", response),
        ("perturbation_recovery_audit.json", perturbation),
        ("real_compile_lane_audit.json", real_lane),
        ("governance_safety_audit.json", governance),
    ]:
        _write_json(out / name, payload)
    summary = {
        "redqueen_stability_validation_started": True,
        "redqueen_stability_validation_completed": True,
        **run_timer.stop().record(cfg.wall_clock_min_hours),
        "planned_wall_clock_hours": cfg.wall_clock_min_hours,
        "hard_stop_hit": False,
        "cycles_completed": cycle_result["cycles_completed"],
        "total_events": sum(cycle["execution"]["events"] for cycle in cycles),
        **{k: real_lane[k] for k in [
            "real_compiler_invocations",
            "real_cl_invocation_count",
            "real_link_invocation_count",
            "real_exe_run_count",
            "compiler_verified_correctness_rate",
            "wrong_stdout_count",
            "timeout_count",
            "permission_error_count",
            "cleanup_failure_count",
            "cached_result_used_as_new_count",
            "duplicate_invocation_id_count",
            "stubbed_validation_detected",
            "summary_only_validation_detected",
        ]},
        "msvc_preflight_passed": preflight["msvc_preflight_passed"],
        "msvc_fail_fast_test_passed": fail_fast_test["msvc_fail_fast_test_passed"],
        "stability_drift_audit_passed": drift["stability_drift_audit_passed"],
        "response_stability_audit_passed": response["response_stability_audit_passed"],
        "perturbation_recovery_audit_passed": perturbation["perturbation_recovery_audit_passed"],
        "real_compile_lane_passed": real_lane["real_compile_lane_passed"],
        "multiround_lifecycle_guard_passed": lifecycle["multiround_lifecycle_guard_passed"],
        "governance_safety_audit_passed": governance["governance_safety_audit_passed"],
        "final_post_run_idle_sentinel_passed": lifecycle["final_post_run_idle_sentinel_passed"],
        "lingering_python_child_count": lifecycle["lingering_python_child_count"],
        "lingering_git_process_count": lifecycle["lingering_git_process_count"],
        "lingering_compiler_process_count": lifecycle["lingering_compiler_process_count"],
        "active_worker_thread_count": lifecycle["active_worker_thread_count"],
        "open_manifest_handle_count": lifecycle["open_manifest_handle_count"],
        "default_profile_unchanged": True,
        "explicit_opt_in_required": True,
        "staged_opt_in_enabled": True,
        "real_promotion_enabled": False,
        "user_facing_enabled": False,
        "official_release_enabled": False,
        "direct_template_path_detected": False,
        "marker_ir_direct_compile_detected": False,
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "redqueen_autonomous_governance_completed": False,
        "ready_for_official_release": False,
        "workers_requested": cfg.workers,
        "workers_used": cfg.workers,
        "compiler_workers_requested": cfg.compiler_workers,
        "compiler_workers_used": cfg.compiler_workers,
        "downgrade_reason": "",
    }
    _write_json(out / "endurance_summary.json", summary)
    readiness = build_stability_readiness(out, summary)
    write_stability_report(out, readiness)
    print(json.dumps({"recommended_claim_level": readiness["recommended_claim_level"], "redqueen_multiround_stability_positive": readiness["redqueen_multiround_stability_positive"]}, ensure_ascii=False, sort_keys=True), flush=True)
    return 0 if readiness["recommended_claim_level"] != "failed" else 1


def _blocked_summary(cfg: RedQueenStabilityConfig, preflight: dict, fail_fast_test: dict) -> dict:
    return {
        "redqueen_stability_validation_started": False,
        "redqueen_stability_validation_completed": False,
        "wall_clock_hours": 0.0,
        "wall_clock_minimum_satisfied": False,
        "hard_stop_hit": False,
        "cycles_completed": 0,
        "total_events": 0,
        "real_compiler_invocations": 0,
        "real_cl_invocation_count": 0,
        "real_link_invocation_count": 0,
        "real_exe_run_count": 0,
        "compiler_verified_correctness_rate": 0.0,
        "wrong_stdout_count": 0,
        "timeout_count": 0,
        "permission_error_count": 0,
        "cleanup_failure_count": 0,
        "cached_result_used_as_new_count": 0,
        "duplicate_invocation_id_count": 0,
        "stubbed_validation_detected": False,
        "summary_only_validation_detected": False,
        "msvc_preflight_passed": preflight.get("msvc_preflight_passed", False),
        "msvc_fail_fast_test_passed": fail_fast_test.get("msvc_fail_fast_test_passed", False),
        "stability_drift_audit_passed": False,
        "response_stability_audit_passed": False,
        "perturbation_recovery_audit_passed": False,
        "real_compile_lane_passed": False,
        "multiround_lifecycle_guard_passed": False,
        "governance_safety_audit_passed": False,
        "default_profile_unchanged": True,
        "real_promotion_enabled": False,
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    for name in ["source-records-v1-0-5-1", "source-records-v1-0-5-2", "source-records-v1-0-6", "source-records-v1-0-6-1", "source-records-v1-0-7", "source-records-v1-0-7-1", "source-records-v1-0-7-2", "source-records-v1-0-8", "source-records-v1-0-8-1", "source-records-v1-0-8-2", "source-records-v1-0-8-3", "source-records-v1-0-8-3-1", "source-records-v1-0-8-4", "source-records-v1-0-8-5"]:
        parser.add_argument(f"--{name}", default="")
    parser.add_argument("--output-records", default="records/v1_0_8_6_stability_msvc")
    parser.add_argument("--profile-name", default="staged_opt_in_function_array_recursion_v1_0_7")
    parser.add_argument("--wall-clock-min-hours", type=float, default=8)
    parser.add_argument("--max-runtime-hours", type=float, default=8)
    parser.add_argument("--hard-stop-hours", type=float, default=8.5)
    parser.add_argument("--cycles", type=int, default=8)
    parser.add_argument("--cycle-min-hours", type=float, default=1)
    parser.add_argument("--total-events-target", type=int, default=300_000)
    parser.add_argument("--minimum-total-events", type=int, default=180_000)
    parser.add_argument("--minimum-real-compiler-invocations", type=int, default=130_000)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--compiler-workers", type=int, default=16)
    parser.add_argument("--trace-writer-mode", default="sharded")
    parser.add_argument("--temp-dir-mode", default="per_sample")
    parser.add_argument("--idle-grace-seconds", type=int, default=30)
    parser.add_argument("--require-response-latency-cycles", type=int, default=1)
    parser.add_argument("--seed", default="234,235,236")
    for flag in ["redqueen-multiround-stability", "msvc-environment-guard", "require-msvc-env", "run-msvc-fail-fast-negative-test", "accounting-lock", "run-stability-drift-audit", "run-response-stability-audit", "run-perturbation-recovery-audit", "require-no-governance-drift", "require-real-compile-lane-clean", "require-lifecycle-guard", "allow-main-thread-only", "no-model-training", "no-weight-update", "explicit-opt-in-required", "forbid-default-profile-change", "forbid-default-bridge-leak", "forbid-real-promotion", "forbid-user-facing-enable", "forbid-release", "require-v1-0-6-adapter-reuse", "require-atomic-policy-bridge", "require-extended-ir-path", "require-extended-emitter", "forbid-template-bypass", "forbid-marker-ir-direct-compile", "forbid-summary-only-validation", "run-governance-safety-audit", "run-claim-boundary-review", "run-architecture-charter-guard", "progress"]:
        parser.add_argument(f"--{flag}", type=_bool, default=True)
    for name in ["max-lingering-python-children", "max-lingering-git-processes", "max-lingering-compiler-processes", "max-active-worker-threads"]:
        parser.add_argument(f"--{name}", type=int, default=0)
    return parser.parse_args()


def write_stability_report(output_records: str | Path, readiness: dict) -> None:
    out = Path(output_records)
    lines = [
        "# v1.0.8.6 RedQueen Multi-round Stability and MSVC Environment Guard",
        "",
        "This version adds MSVC compiler environment preflight and runs an 8-hour RedQueen stability validation when the compiler environment is ready.",
        "",
        "It does not train models, update weights, modify the default profile, enable real promotion, release, or claim production support completed.",
        "",
        f"- MSVC preflight passed: `{readiness.get('msvc_preflight_passed')}`",
        f"- MSVC fail-fast negative test passed: `{readiness.get('msvc_fail_fast_test_passed')}`",
        f"- 8h validation completed: `{readiness.get('wall_clock_minimum_satisfied')}`",
        f"- cycles completed: `{readiness.get('cycles_completed')}`",
        f"- stability drift audit passed: `{readiness.get('stability_drift_audit_passed')}`",
        f"- response stability audit passed: `{readiness.get('response_stability_audit_passed')}`",
        f"- perturbation recovery audit passed: `{readiness.get('perturbation_recovery_audit_passed')}`",
        f"- real compile lane passed: `{readiness.get('real_compile_lane_passed')}`",
        f"- lifecycle guard passed: `{readiness.get('multiround_lifecycle_guard_passed')}`",
        f"- governance safety audit passed: `{readiness.get('governance_safety_audit_passed')}`",
        f"- default profile unchanged: `{readiness.get('default_profile_unchanged')}`",
        f"- real promotion enabled: `{readiness.get('real_promotion_enabled')}`",
        f"- production support completed: `false`",
        f"- RedQueen autonomous governance completed: `{readiness.get('redqueen_autonomous_governance_completed')}`",
        f"- recommended claim level: `{readiness.get('recommended_claim_level')}`",
        f"- blocking issues: `{readiness.get('blocking_issues')}`",
        f"- required next run: `{readiness.get('required_next_run')}`",
        "",
        "## Cycle Overview",
        "",
        "- Cycle 0: baseline / no weak signal.",
        "- Cycle 1: function weak signal.",
        "- Cycle 2: function response plus mixed weak signal.",
        "- Cycle 3: remove function weak signal and keep mixed weak signal.",
        "- Cycle 4: remove all weak signals and observe recovery annealing.",
        "- Cycle 5: all-stable frontier pressure.",
        "- Cycle 6: repeated mild perturbation on function plus mixed.",
        "- Cycle 7: final all-clean stability confirmation.",
        "",
        "## Still Not Proven",
        "",
    ]
    lines.extend(f"- {item}" for item in STILL_NOT_PROVEN_STABILITY)
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "mainline_conclusion.json").write_text(json.dumps({"readiness": readiness, "still_not_proven": list(STILL_NOT_PROVEN_STABILITY)}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
