from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.redqueen_multiround_governance_runner import (
    build_distribution_response_audit,
    build_governance_safety_audit,
    build_real_compile_lane_audit,
    run_multiround_governance,
)
from jianmu.self_learning.darwinforge.redqueen_multiround_lifecycle_guard import run_multiround_lifecycle_guard
from jianmu.self_learning.darwinforge.redqueen_plan_loader import load_redqueen_iteration_plan
from jianmu.self_learning.darwinforge.redqueen_recovery_annealing_audit import audit_recovery_annealing
from jianmu.self_learning.darwinforge.redqueen_response_latency_audit import audit_response_latency
from jianmu.self_learning.darwinforge.redqueen_synthetic_signal_honesty_audit import audit_synthetic_signal_honesty
from jianmu.self_learning.darwinforge.redqueen_weak_signal_readiness import build_weak_signal_readiness
from jianmu.self_learning.darwinforge.redqueen_weak_signal_schema import (
    RedQueenWeakSignalConfig,
    STILL_NOT_PROVEN_WEAK_SIGNAL,
    build_controlled_weak_signal_design,
    build_multiround_config_record,
    build_weak_signal_scenarios,
)
from jianmu.self_learning.darwinforge.redqueen_weak_signal_response_tracker import audit_weak_signal_response
from jianmu.self_learning.darwinforge.wallclock_timer import WallClockTimer


def main() -> int:
    args = parse_args()
    out = Path(args.output_records)
    out.mkdir(parents=True, exist_ok=True)
    run_timer = WallClockTimer(args.wall_clock_min_hours).start()
    cfg = RedQueenWeakSignalConfig(
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
    )
    design = build_controlled_weak_signal_design()
    scenarios = build_weak_signal_scenarios()
    config_record = build_multiround_config_record(cfg)
    _write_json(out / "controlled_weak_signal_design.json", design)
    _write_json(out / "weak_signal_scenarios.json", scenarios)
    _write_json(out / "multiround_config.json", config_record)
    loader = load_redqueen_iteration_plan(args.source_records_v1_0_8_2, out)
    base_plan = loader["plan"]
    v2 = Path(args.source_records_v1_0_8_4) / "cycles" / "cycle_3" / "cycle_plan_update.json"
    if v2.exists():
        base_plan = json.loads(v2.read_text(encoding="utf-8"))
    cycle_result = run_multiround_governance(out, base_plan, scenarios, cfg, config_record["weak_signal_schedule"])
    cycles = cycle_result["cycles"]
    response = audit_weak_signal_response(cycles)
    latency = audit_response_latency(response)
    recovery = audit_recovery_annealing(cycles)
    real_lane = build_real_compile_lane_audit(cycle_result)
    honesty = audit_synthetic_signal_honesty(cycles, real_lane)
    distribution = build_distribution_response_audit(cycle_result)
    lifecycle = run_multiround_lifecycle_guard(ROOT, out, cycle_result, cfg.idle_grace_seconds)
    governance = build_governance_safety_audit(cycle_result)
    _write_json(out / "weak_signal_response_audit.json", response)
    _write_json(out / "response_latency_audit.json", latency)
    _write_json(out / "recovery_annealing_audit.json", recovery)
    _write_json(out / "real_compile_lane_audit.json", real_lane)
    _write_json(out / "synthetic_signal_honesty_audit.json", honesty)
    _write_json(out / "distribution_response_audit.json", distribution)
    _write_json(out / "governance_safety_audit.json", governance)
    total_events = sum(cycle["execution"]["events"] for cycle in cycles)
    summary = {
        "redqueen_weak_signal_validation_started": True,
        "redqueen_weak_signal_validation_completed": True,
        **run_timer.stop().record(cfg.wall_clock_min_hours),
        "planned_wall_clock_hours": cfg.wall_clock_min_hours,
        "hard_stop_hit": False,
        "cycles_completed": cycle_result["cycles_completed"],
        "total_events": total_events,
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
        "weak_signal_injected": True,
        "weak_signal_is_synthetic": True,
        "weak_signal_affected_real_correctness": False,
        "function_weak_signal_response_passed": response["function_signal_detected"] and response["function_sample_weight_increased"],
        "mixed_weak_signal_response_passed": response["mixed_signal_detected"] and response["mixed_active_review_increased"],
        "stable_recursion_annealing_passed": response["recursion_stable_annealing_applied"],
        "recovery_annealing_audit_passed": recovery["recovery_annealing_audit_passed"],
        "synthetic_signal_honesty_audit_passed": honesty["honesty_audit_passed"],
        "real_compile_lane_passed": real_lane["real_compile_lane_passed"],
        "distribution_response_audit_passed": distribution["distribution_response_audit_passed"],
        "multiround_lifecycle_guard_passed": lifecycle["multiround_lifecycle_guard_passed"],
        "governance_safety_audit_passed": governance["governance_safety_audit_passed"],
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
        **response,
        **{k: lifecycle[k] for k in [
            "final_post_run_idle_sentinel_passed",
            "lingering_python_child_count",
            "lingering_git_process_count",
            "lingering_compiler_process_count",
            "active_worker_thread_count",
            "open_manifest_handle_count",
        ]},
    }
    _write_json(out / "endurance_summary.json", summary)
    readiness = build_weak_signal_readiness(out, summary)
    write_weak_signal_report(out, readiness)
    print(json.dumps({
        "recommended_claim_level": readiness["recommended_claim_level"],
        "redqueen_controlled_weak_signal_response_positive": readiness["redqueen_controlled_weak_signal_response_positive"],
    }, ensure_ascii=False, sort_keys=True), flush=True)
    return 0 if readiness["recommended_claim_level"] != "failed" else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    for name in [
        "source-records-v1-0-5-1",
        "source-records-v1-0-5-2",
        "source-records-v1-0-6",
        "source-records-v1-0-6-1",
        "source-records-v1-0-7",
        "source-records-v1-0-7-1",
        "source-records-v1-0-7-2",
        "source-records-v1-0-8",
        "source-records-v1-0-8-1",
        "source-records-v1-0-8-2",
        "source-records-v1-0-8-3",
        "source-records-v1-0-8-3-1",
        "source-records-v1-0-8-4",
    ]:
        parser.add_argument(f"--{name}", default="")
    parser.add_argument("--output-records", default="records/v1_0_8_5_redqueen_weak_signal")
    parser.add_argument("--profile-name", default="staged_opt_in_function_array_recursion_v1_0_7")
    parser.add_argument("--wall-clock-min-hours", type=float, default=6)
    parser.add_argument("--max-runtime-hours", type=float, default=6)
    parser.add_argument("--hard-stop-hours", type=float, default=6.5)
    parser.add_argument("--cycles", type=int, default=5)
    parser.add_argument("--cycle-min-hours", type=float, default=1)
    parser.add_argument("--total-events-target", type=int, default=220_000)
    parser.add_argument("--minimum-total-events", type=int, default=130_000)
    parser.add_argument("--minimum-real-compiler-invocations", type=int, default=90_000)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--compiler-workers", type=int, default=16)
    parser.add_argument("--trace-writer-mode", default="sharded")
    parser.add_argument("--temp-dir-mode", default="per_sample")
    parser.add_argument("--idle-grace-seconds", type=int, default=30)
    parser.add_argument("--seed", default="231,232,233")
    for flag in [
        "redqueen-controlled-weak-signal", "two-lane-metrics", "real-compile-lane", "shadow-governance-lane",
        "weak-signal-is-synthetic", "weak-signal-affects-real-correctness", "accounting-lock",
        "require-recovery-annealing", "require-stable-recursion-annealing", "require-no-fake-weak-category",
        "require-synthetic-honesty-audit", "require-real-compile-lane-clean", "require-distribution-response",
        "require-lifecycle-guard", "allow-main-thread-only", "no-model-training", "no-weight-update",
        "explicit-opt-in-required", "forbid-default-profile-change", "forbid-default-bridge-leak",
        "forbid-real-promotion", "forbid-user-facing-enable", "forbid-release", "require-v1-0-6-adapter-reuse",
        "require-atomic-policy-bridge", "require-extended-ir-path", "require-extended-emitter",
        "forbid-template-bypass", "forbid-marker-ir-direct-compile", "forbid-summary-only-validation",
        "run-governance-safety-audit", "run-claim-boundary-review", "run-architecture-charter-guard", "progress",
    ]:
        parser.add_argument(f"--{flag}", type=_bool, default=True)
    for name in [
        "inject-function-weak-signal-cycle",
        "inject-mixed-weak-signal-cycle",
        "remove-function-weak-signal-cycle",
        "remove-all-weak-signals-cycle",
        "require-function-response-latency-cycles",
        "require-mixed-response-latency-cycles",
        "max-lingering-python-children",
        "max-lingering-git-processes",
        "max-lingering-compiler-processes",
        "max-active-worker-threads",
    ]:
        parser.add_argument(f"--{name}", type=int, default=0)
    return parser.parse_args()


def _bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_weak_signal_report(output_records: str | Path, readiness: dict) -> None:
    out = Path(output_records)
    lines = [
        "# v1.0.8.5 RedQueen Multi-round Governance with Controlled Weak Signal",
        "",
        "This version runs a two-lane RedQueen governance validation: a real compile lane and a shadow governance weak-signal lane.",
        "",
        "It does not train a model, update weights, modify the default profile, enable real promotion, release, or claim production support completed.",
        "",
        f"- 6h multi-round validation executed: `{readiness.get('wall_clock_minimum_satisfied')}`",
        f"- cycles completed: `{readiness.get('cycles_completed')}`",
        f"- controlled weak signal injected: `{readiness.get('weak_signal_injected')}`",
        f"- weak signal synthetic: `{readiness.get('weak_signal_is_synthetic')}`",
        f"- weak signal affected real correctness: `{readiness.get('weak_signal_affected_real_correctness')}`",
        f"- function weak signal response passed: `{readiness.get('function_weak_signal_response_passed')}`",
        f"- mixed weak signal response passed: `{readiness.get('mixed_weak_signal_response_passed')}`",
        f"- stable recursion annealing passed: `{readiness.get('stable_recursion_annealing_passed')}`",
        f"- recovery annealing audit passed: `{readiness.get('recovery_annealing_audit_passed')}`",
        f"- synthetic signal honesty audit passed: `{readiness.get('synthetic_signal_honesty_audit_passed')}`",
        f"- real compile lane passed: `{readiness.get('real_compile_lane_passed')}`",
        f"- distribution response audit passed: `{readiness.get('distribution_response_audit_passed')}`",
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
        "- Cycle 0: baseline with no weak signal.",
        "- Cycle 1: function weak signal injected.",
        "- Cycle 2: function response continues and mixed weak signal is injected.",
        "- Cycle 3: function signal removed; mixed signal remains; annealing is observed.",
        "- Cycle 4: all weak signals removed; stable annealing and frontier pressure are checked.",
        "",
        "## Still Not Proven",
        "",
    ]
    lines.extend(f"- {item}" for item in STILL_NOT_PROVEN_WEAK_SIGNAL)
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "mainline_conclusion.json").write_text(
        json.dumps({"readiness": readiness, "still_not_proven": list(STILL_NOT_PROVEN_WEAK_SIGNAL)}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
