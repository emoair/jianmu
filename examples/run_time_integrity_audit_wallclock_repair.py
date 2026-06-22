from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.planned_vs_actual_time_detector import audit_planned_vs_actual_time_code
from jianmu.self_learning.darwinforge.redqueen_plan_loader import load_redqueen_iteration_plan
from jianmu.self_learning.darwinforge.time_integrity_audit import build_time_integrity_audit_summary
from jianmu.self_learning.darwinforge.time_integrity_guard import build_time_integrity_guard
from jianmu.self_learning.darwinforge.time_integrity_readiness import build_time_integrity_readiness
from jianmu.self_learning.darwinforge.time_integrity_schema import TIME_REPAIR_STILL_NOT_PROVEN, TimeRepairValidationConfig
from jianmu.self_learning.darwinforge.v1_0_8_6_time_claim_auditor import audit_v1_0_8_6_time_claim
from jianmu.self_learning.darwinforge.wallclock_repair_validation import run_wallclock_repair_validation
from jianmu.self_learning.darwinforge.wallclock_timer import build_wallclock_timer_contract


def main() -> int:
    args = parse_args()
    out = Path(args.output_records)
    out.mkdir(parents=True, exist_ok=True)
    time_claim = audit_v1_0_8_6_time_claim(args.source_records_v1_0_8_6)
    code_audit = audit_planned_vs_actual_time_code(ROOT)
    timer_contract = build_wallclock_timer_contract()
    guard = build_time_integrity_guard()
    _write_json(out / "v1_0_8_6_time_claim_audit.json", time_claim)
    _write_json(out / "planned_vs_actual_time_code_audit.json", code_audit)
    _write_json(out / "wallclock_timer_contract.json", timer_contract)
    _write_json(out / "time_integrity_guard.json", guard)
    _write_json(out / "time_integrity_audit.json", build_time_integrity_audit_summary(time_claim, code_audit))
    loader = load_redqueen_iteration_plan(args.source_records_v1_0_8_6.replace("v1_0_8_6_stability_msvc", "v1_0_8_2_redqueen_bootstrap"), out)
    plan = loader.get("plan", {})
    if not plan:
        plan = {"category_weights": {}, "difficulty_levels": {}, "active_review_allocations": {}, "shape_diversity_targets": {}, "boundary_recheck_targets": {}, "rollback_recheck_targets": {}, "replay_recheck_targets": {}}
    cfg = TimeRepairValidationConfig(
        planned_wall_clock_hours=args.wall_clock_min_hours,
        max_runtime_hours=args.max_runtime_hours,
        hard_stop_hours=args.hard_stop_hours,
        cycles=args.cycles,
        planned_cycle_min_hours=args.cycle_min_hours,
        target_events=args.target_events,
        minimum_events=args.minimum_events,
        minimum_real_compiler_invocations=args.minimum_real_compiler_invocations,
        heartbeat_interval_seconds=args.heartbeat_interval_seconds,
        heartbeat_interval_events=args.heartbeat_interval_events,
        idle_grace_seconds=args.idle_grace_seconds,
        workers=args.workers,
        compiler_workers=args.compiler_workers,
    )
    validation = run_wallclock_repair_validation(ROOT, out, plan, cfg) if args.run_repair_validation else {"summary": {"repair_validation_passed": False}, "heartbeat_contract": {"heartbeat_contract_passed": False}, "lifecycle": {"lifecycle_recheck_passed": False}}
    heartbeat_contract = validation["heartbeat_contract"]
    _write_json(out / "wallclock_heartbeat_contract.json", heartbeat_contract)
    repair = validation["summary"]
    payload = {
        "v1_0_8_6_time_claim_audited": True,
        **{k: time_claim[k] for k in [
            "v1_0_8_6_endurance_claim_accepted",
            "v1_0_8_6_endurance_claim_downgraded",
            "time_claim_integrity_status",
            "downgrade_reason",
        ]},
        **code_audit,
        **timer_contract,
        "heartbeat_contract_passed": heartbeat_contract["heartbeat_contract_passed"],
        **guard,
        **repair,
        "lifecycle_recheck_passed": repair.get("lifecycle_clean", False),
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "redqueen_autonomous_governance_completed": False,
        "ready_for_official_release": False,
    }
    readiness = build_time_integrity_readiness(out, payload)
    write_mainline_conclusion(out, time_claim, code_audit, repair, readiness)
    print(json.dumps({"recommended_claim_level": readiness["recommended_claim_level"], "actual_wall_clock_hours": readiness.get("actual_wall_clock_hours")}, ensure_ascii=False, sort_keys=True), flush=True)
    return 0 if readiness["recommended_claim_level"] != "failed" else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--source-records-v1-0-8-6", default="records/v1_0_8_6_stability_msvc")
    parser.add_argument("--output-records", default="records/v1_0_8_6_1_time_integrity")
    parser.add_argument("--wall-clock-min-hours", type=float, default=2)
    parser.add_argument("--max-runtime-hours", type=float, default=2)
    parser.add_argument("--hard-stop-hours", type=float, default=2.25)
    parser.add_argument("--cycles", type=int, default=2)
    parser.add_argument("--cycle-min-hours", type=float, default=1)
    parser.add_argument("--target-events", type=int, default=70_000)
    parser.add_argument("--minimum-events", type=int, default=40_000)
    parser.add_argument("--minimum-real-compiler-invocations", type=int, default=25_000)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--compiler-workers", type=int, default=16)
    parser.add_argument("--heartbeat-interval-seconds", type=int, default=300)
    parser.add_argument("--heartbeat-interval-events", type=int, default=10_000)
    parser.add_argument("--idle-grace-seconds", type=int, default=30)
    parser.add_argument("--seed", default="237,238,239")
    for flag in ["audit-v1-0-8-6-time-claim", "audit-code-planned-vs-actual-time", "repair-wallclock-timer", "use-monotonic-clock", "record-utc-start-end", "record-cycle-timestamps", "record-heartbeat", "reject-planned-time-as-actual", "run-repair-validation", "require-cycle-actual-elapsed", "require-heartbeat-span-match", "require-lifecycle-recheck", "accounting-lock", "allow-main-thread-only", "no-model-training", "no-weight-update", "explicit-opt-in-required", "forbid-default-profile-change", "forbid-real-promotion", "forbid-release", "run-claim-boundary-review", "run-architecture-charter-guard", "progress"]:
        parser.add_argument(f"--{flag}", type=_bool, default=True)
    for name in ["require-actual-elapsed-seconds", "max-lingering-python-children", "max-lingering-git-processes", "max-lingering-compiler-processes", "max-active-worker-threads"]:
        parser.add_argument(f"--{name}", type=int, default=0)
    parser.add_argument("--trace-writer-mode", default="sharded")
    parser.add_argument("--temp-dir-mode", default="per_sample")
    return parser.parse_args()


def write_mainline_conclusion(out: Path, time_claim: dict, code_audit: dict, repair: dict, readiness: dict) -> None:
    lines = [
        "# v1.0.8.6.1 Time Integrity Audit and Wall-clock Repair",
        "",
        "This version audits the v1.0.8.6 8h claim, repairs planned-as-actual wall-clock bugs, adds monotonic/UTC/cycle/heartbeat timing, and validates the repair with a real 2h wall-clock run.",
        "",
        "It does not release, enable real promotion, modify default production support, claim production support completed, or restore the v1.0.8.6 8h claim.",
        "",
        f"- v1.0.8.6 8h claim accepted: `{time_claim.get('v1_0_8_6_endurance_claim_accepted')}`",
        f"- v1.0.8.6 downgraded: `{time_claim.get('v1_0_8_6_endurance_claim_downgraded')}`",
        f"- downgrade reason: `{time_claim.get('downgrade_reason')}`",
        f"- planned-as-actual patterns found: `{code_audit.get('dangerous_time_patterns_found')}`",
        f"- fixes applied: `{code_audit.get('fixes_applied')}`",
        f"- time.monotonic used: `{readiness.get('monotonic_source_used')}`",
        f"- UTC start/end recorded: `{readiness.get('utc_timestamps_recorded')}`",
        f"- cycle elapsed recorded: `{readiness.get('cycle_timing_recorded')}`",
        f"- heartbeat contract passed: `{readiness.get('heartbeat_contract_passed')}`",
        f"- 2h repair validation passed: `{repair.get('repair_validation_passed')}`",
        f"- actual wall-clock hours: `{repair.get('actual_wall_clock_hours')}`",
        f"- actual elapsed seconds: `{repair.get('actual_elapsed_seconds')}`",
        f"- lifecycle recheck passed: `{repair.get('lifecycle_clean')}`",
        f"- default profile unchanged: `{readiness.get('default_profile_unchanged')}`",
        f"- real promotion enabled: `{readiness.get('real_promotion_enabled')}`",
        f"- production support completed: `false`",
        f"- recommended claim level: `{readiness.get('recommended_claim_level')}`",
        f"- blocking issues: `{readiness.get('blocking_issues')}`",
        f"- required next run: `{readiness.get('required_next_run')}`",
        "",
        "## Still Not Proven",
        "",
    ]
    lines.extend(f"- {item}" for item in TIME_REPAIR_STILL_NOT_PROVEN)
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "mainline_conclusion.json").write_text(json.dumps({"readiness": readiness, "still_not_proven": list(TIME_REPAIR_STILL_NOT_PROVEN)}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
