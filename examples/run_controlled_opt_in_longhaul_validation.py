from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.controlled_opt_in_longhaul_readiness import build_controlled_opt_in_longhaul_readiness
from jianmu.self_learning.darwinforge.controlled_opt_in_longhaul_schema import ControlledOptInLonghaulConfig, STILL_NOT_PROVEN
from jianmu.self_learning.darwinforge.opt_in_heldout_validation_set import build_heldout_validation_set
from jianmu.self_learning.darwinforge.opt_in_longhaul_coverage_review import run_longhaul_coverage_review
from jianmu.self_learning.darwinforge.opt_in_longhaul_execution import run_opt_in_longhaul_execution
from jianmu.self_learning.darwinforge.opt_in_longhaul_replay import run_longhaul_replay
from jianmu.self_learning.darwinforge.opt_in_longhaul_rollback import run_longhaul_rollback_review
from jianmu.self_learning.darwinforge.opt_in_regression_guard import run_opt_in_regression_guard


def main() -> int:
    args = parse_args()
    out = Path(args.output_records)
    out.mkdir(parents=True, exist_ok=True)
    cfg = ControlledOptInLonghaulConfig(
        profile_name=args.profile_name,
        wall_clock_min_hours=args.wall_clock_min_hours,
        max_runtime_hours=args.max_runtime_hours,
        hard_stop_hours=args.hard_stop_hours,
        workers=args.workers,
        compiler_workers=args.compiler_workers,
        replay_samples=args.replay_samples,
        replay_minimum_required=args.replay_minimum_required,
        rollback_cycles=args.rollback_cycles,
        samples_per_rollback_cycle=args.samples_per_rollback_cycle,
        target_real_validation_events=args.target_real_validation_events,
        minimum_real_validation_events=args.minimum_real_validation_events,
        minimum_real_compiler_invocations=args.minimum_real_compiler_invocations,
        minimum_unique_compile_units=args.minimum_unique_compile_units,
        target_unique_compile_units=args.target_unique_compile_units,
        minimum_source_sha256_unique=args.minimum_source_sha256_unique,
        target_source_sha256_unique=args.target_source_sha256_unique,
    )
    heldout = build_heldout_validation_set(out, args.profile_name, _first_seed(args.seed))
    _checkpoint(out, "heldout_built")
    targets = cfg.target_counts(args.default_blocking_target, args.malformed_opt_in_blocking_target, args.arithmetic_target, args.function_target, args.array_target, args.function_array_target, args.recursion_target, args.mixed_target, args.opt_out_rollback_target, args.post_rollback_default_blocking_target)
    _checkpoint(out, "targets_built")
    execution = run_opt_in_longhaul_execution(out, cfg, targets, _first_seed(args.seed), args.progress)
    _checkpoint(out, "execution_completed")
    rows = execution.pop("rows")
    execution.pop("heartbeats", None)
    accounting = {key: execution[key] for key in ["real_validation_events", "real_compiler_invocations", "real_cl_invocation_count", "real_link_invocation_count", "real_exe_run_count", "unique_compile_unit_count", "source_sha256_unique_count", "cached_result_used_as_new_count", "duplicate_invocation_id_count", "stubbed_validation_detected", "summary_only_validation_detected", "syntax_filter_used_as_correctness_evidence", "wrong_stdout_count", "timeout_count", "permission_error_count", "cleanup_failure_count", "thread_safety_issue_detected", "trace_write_error_count", "temp_dir_collision_count"] if key in execution}
    coverage = run_longhaul_coverage_review(out, rows, args.minimum_unique_compile_units, args.target_unique_compile_units)
    replay = run_longhaul_replay(out, rows, args.replay_samples, args.workers, args.compiler_workers)
    rollback = run_longhaul_rollback_review(out, args.rollback_cycles, args.samples_per_rollback_cycle)
    regression = run_opt_in_regression_guard(out)
    regression_path = out / "opt_in_regression_guard.json"
    if regression_path.exists():
        regression_path.replace(out / "longhaul_regression_guard.json")
    readiness = build_controlled_opt_in_longhaul_readiness(out, heldout, execution, accounting, coverage, replay, rollback, regression)
    write_mainline(out, readiness)
    print(json.dumps({"output_records": str(out), "recommended_claim_level": readiness["recommended_claim_level"], "real_validation_events": readiness["real_validation_events"]}, ensure_ascii=False, sort_keys=True))
    return 0


def _checkpoint(out: Path, phase: str) -> None:
    checkpoint_path = out / "longhaul_runner_checkpoints.jsonl"
    payload = {"phase": phase}
    with checkpoint_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)


def write_mainline(out: Path, readiness: dict) -> None:
    lines = [
        "# v1.0.7.1 Controlled Opt-in Longhaul Validation",
        "",
        "## What This Version Did",
        "Ran 8-hour longhaul validation for the v1.0.7 staged opt-in profile with heldout, replay, rollback, coverage, accounting, guard heartbeat, and trace pack evidence.",
        "",
        "## What This Version Did Not Do",
        "It did not train or update model weights, modify the default profile, enable real promotion, enable official release, claim production support, add natural language, or add a new capability frontier.",
        "",
        "## Mainline Result",
    ]
    for key in ["longhaul_validation_completed", "wall_clock_hours", "heldout_set_created", "no_model_training", "no_weight_update", "default_profile_unchanged", "explicit_opt_in_required", "real_promotion_enabled", "default_blocking_success_rate", "malformed_opt_in_blocking_success_rate", "function_opt_in_success_rate", "array_opt_in_success_rate", "function_array_opt_in_success_rate", "structured_recursion_opt_in_success_rate", "mixed_opt_in_success_rate", "opt_out_rollback_success_rate", "real_validation_events", "real_compiler_invocations", "unique_compile_unit_count", "coverage_expansion_successful", "replay_success_rate", "rollback_review_passed", "regression_guard_passed", "trace_pack_replayable", "ready_for_controlled_opt_in_support_candidate_review", "production_function_support_completed", "production_array_support_completed", "production_recursion_support_completed", "recommended_claim_level", "blocking_issues", "required_next_run"]:
        lines.append(f"- {key}: {readiness.get(key)}")
    lines.extend(["", "## Still Not Proven"])
    lines.extend(f"- {item}" for item in STILL_NOT_PROVEN)
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "mainline_conclusion.json").write_text(json.dumps({"readiness": readiness}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    for name in ["records-root", "docs-root", "source-records-v1-0-5-1", "source-records-v1-0-5-2", "source-records-v1-0-6", "source-records-v1-0-6-1", "source-records-v1-0-7"]:
        p.add_argument(f"--{name}", default="")
    p.add_argument("--output-records", default="records/v1_0_7_1_longhaul")
    p.add_argument("--profile-name", default="staged_opt_in_function_array_recursion_v1_0_7")
    p.add_argument("--longhaul-validation", type=_bool, default=True)
    p.add_argument("--heldout-validation", type=_bool, default=True)
    p.add_argument("--no-model-training", type=_bool, default=True)
    p.add_argument("--no-weight-update", type=_bool, default=True)
    p.add_argument("--explicit-opt-in-required", type=_bool, default=True)
    p.add_argument("--forbid-default-profile-change", type=_bool, default=True)
    p.add_argument("--forbid-default-bridge-leak", type=_bool, default=True)
    p.add_argument("--forbid-real-promotion", type=_bool, default=True)
    p.add_argument("--forbid-user-facing-enable", type=_bool, default=True)
    p.add_argument("--forbid-release", type=_bool, default=True)
    p.add_argument("--wall-clock-min-hours", type=float, default=8.0)
    p.add_argument("--max-runtime-hours", type=float, default=8.0)
    p.add_argument("--hard-stop-hours", type=float, default=8.5)
    p.add_argument("--workers", type=int, default=16)
    p.add_argument("--compiler-workers", type=int, default=16)
    p.add_argument("--trace-writer-mode", default="sharded")
    p.add_argument("--temp-dir-mode", default="per_sample")
    p.add_argument("--accounting-lock", type=_bool, default=True)
    p.add_argument("--target-real-validation-events", type=int, default=270000)
    p.add_argument("--minimum-real-validation-events", type=int, default=120000)
    p.add_argument("--minimum-real-compiler-invocations", type=int, default=90000)
    p.add_argument("--default-blocking-target", type=int, default=20000)
    p.add_argument("--malformed-opt-in-blocking-target", type=int, default=10000)
    p.add_argument("--arithmetic-target", type=int, default=30000)
    p.add_argument("--function-target", type=int, default=35000)
    p.add_argument("--array-target", type=int, default=35000)
    p.add_argument("--function-array-target", type=int, default=35000)
    p.add_argument("--recursion-target", type=int, default=25000)
    p.add_argument("--mixed-target", type=int, default=40000)
    p.add_argument("--opt-out-rollback-target", type=int, default=25000)
    p.add_argument("--post-rollback-default-blocking-target", type=int, default=15000)
    p.add_argument("--rollback-cycles", type=int, default=500)
    p.add_argument("--samples-per-rollback-cycle", type=int, default=5)
    p.add_argument("--replay-samples", type=int, default=5000)
    p.add_argument("--replay-minimum-required", type=int, default=2000)
    p.add_argument("--require-all-categories", type=_bool, default=True)
    p.add_argument("--attempt-coverage-expansion", type=_bool, default=True)
    p.add_argument("--minimum-unique-compile-units", type=int, default=9896)
    p.add_argument("--target-unique-compile-units", type=int, default=12000)
    p.add_argument("--minimum-source-sha256-unique", type=int, default=9896)
    p.add_argument("--target-source-sha256-unique", type=int, default=12000)
    p.add_argument("--require-v1-0-6-adapter-reuse", type=_bool, default=True)
    p.add_argument("--require-atomic-policy-bridge", type=_bool, default=True)
    p.add_argument("--require-extended-ir-path", type=_bool, default=True)
    p.add_argument("--require-extended-emitter", type=_bool, default=True)
    p.add_argument("--forbid-template-bypass", type=_bool, default=True)
    p.add_argument("--forbid-marker-ir-direct-compile", type=_bool, default=True)
    p.add_argument("--forbid-summary-only-validation", type=_bool, default=True)
    p.add_argument("--run-default-blocking-audit", type=_bool, default=True)
    p.add_argument("--run-regression-guard", type=_bool, default=True)
    p.add_argument("--run-longhaul-rollback", type=_bool, default=True)
    p.add_argument("--run-longhaul-replay", type=_bool, default=True)
    p.add_argument("--run-trace-pack-builder", type=_bool, default=True)
    p.add_argument("--run-claim-boundary-review", type=_bool, default=True)
    p.add_argument("--run-architecture-charter-guard", type=_bool, default=True)
    p.add_argument("--progress", type=_bool, default=False)
    p.add_argument("--seed", default="207")
    return p.parse_args()


def _bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return value.lower() in {"1", "true", "yes", "on"}


def _first_seed(value: str) -> int:
    return int(str(value).split(",", 1)[0])


if __name__ == "__main__":
    raise SystemExit(main())
