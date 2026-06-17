from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.coverage_expansion_execution import run_coverage_expansion_execution
from jianmu.self_learning.darwinforge.coverage_expansion_readiness import (
    build_coverage_expansion_readiness,
    build_coverage_expansion_review,
    build_default_blocking_rollback_regression,
)
from jianmu.self_learning.darwinforge.coverage_expansion_schema import CoverageExpansionConfig, STILL_NOT_PROVEN
from jianmu.self_learning.darwinforge.coverage_replay_trace_pack_builder import write_coverage_replay_trace_pack
from jianmu.self_learning.darwinforge.opt_in_shape_diversity_builder import build_shape_diversity_manifest
from jianmu.self_learning.darwinforge.replay_concurrency_repair import run_16_worker_replay, write_replay_concurrency_repair_report


def main() -> int:
    args = parse_args()
    out = Path(args.output_records)
    out.mkdir(parents=True, exist_ok=True)
    cfg = CoverageExpansionConfig(
        profile_name=args.profile_name,
        wall_clock_min_hours=args.wall_clock_min_hours,
        max_runtime_hours=args.max_runtime_hours,
        hard_stop_hours=args.hard_stop_hours,
        workers=args.workers,
        compiler_workers=args.compiler_workers,
        replay_workers=args.replay_workers,
        replay_samples=args.replay_samples,
        replay_minimum_required=args.replay_minimum_required,
        minimum_real_validation_events=args.minimum_real_validation_events,
        minimum_real_compiler_invocations=args.minimum_real_compiler_invocations,
        minimum_unique_compile_units=args.minimum_unique_compile_units,
        target_unique_compile_units=args.target_unique_compile_units,
        minimum_source_sha256_unique=args.minimum_source_sha256_unique,
        target_source_sha256_unique=args.target_source_sha256_unique,
        target_real_validation_events=args.target_real_validation_events,
    )
    _checkpoint(out, "shape_diversity_started")
    shape_manifest = build_shape_diversity_manifest(out, args.target_unique_compile_units, args.target_source_sha256_unique)
    targets = cfg.target_counts(args.default_blocking_target, args.malformed_opt_in_blocking_target, args.arithmetic_target, args.function_target, args.array_target, args.function_array_target, args.recursion_target, args.mixed_target, args.opt_out_rollback_target, args.post_rollback_default_blocking_target)
    _checkpoint(out, "execution_started")
    execution = run_coverage_expansion_execution(out, cfg, targets, _first_seed(args.seed), args.progress)
    rows = execution.pop("rows")
    heartbeats = execution.pop("heartbeats")
    backend_report = execution.pop("backend_report")
    _checkpoint(out, "trace_pack_started")
    trace_pack = write_coverage_replay_trace_pack(out, rows, heartbeats, backend_report)
    repair = write_replay_concurrency_repair_report(out, out / "coverage_replay_trace_pack", args.replay_workers)
    _checkpoint(out, "replay_started")
    replay = run_16_worker_replay(out, rows, args.replay_samples, args.replay_workers, args.compiler_workers)
    _checkpoint(out, "replay_completed")
    accounting = {key: execution[key] for key in [
        "real_validation_events", "real_compiler_invocations", "real_cl_invocation_count", "real_link_invocation_count",
        "real_exe_run_count", "unique_compile_unit_count", "source_sha256_unique_count", "shape_signature_unique_count",
        "cached_result_used_as_new_count", "duplicate_invocation_id_count", "stubbed_validation_detected",
        "summary_only_validation_detected", "syntax_filter_used_as_correctness_evidence", "wrong_stdout_count",
        "timeout_count", "permission_error_count", "cleanup_failure_count", "thread_safety_issue_detected",
        "trace_write_error_count", "temp_dir_collision_count",
    ] if key in execution}
    accounting["replay_worker_timeout_count"] = replay.get("replay_worker_timeout_count", 0)
    (out / "coverage_expansion_accounting.json").write_text(json.dumps(accounting, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    review = build_coverage_expansion_review(out, rows)
    _checkpoint(out, "review_completed")
    guard = build_default_blocking_rollback_regression(out, execution)
    readiness = build_coverage_expansion_readiness(out, shape_manifest, execution, accounting, review, replay, guard, trace_pack, repair)
    _checkpoint(out, "readiness_completed")
    write_mainline(out, readiness)
    _safe_print(json.dumps({"output_records": str(out), "recommended_claim_level": readiness.get("recommended_claim_level"), "unique_compile_unit_count": readiness.get("unique_compile_unit_count"), "replay_16_worker_passed": readiness.get("replay_16_worker_passed")}, ensure_ascii=False, sort_keys=True))
    return 0


def write_mainline(out: Path, readiness: dict) -> None:
    lines = [
        "# v1.0.7.2 Coverage Expansion and Replay Concurrency Repair",
        "",
        "## What This Version Did",
        "Expanded the staged opt-in validation shape pool and repaired 16-worker replay scheduling with shard indexing, worker isolation, heartbeat, and sharded manifests.",
        "",
        "## What This Version Did Not Do",
        "It did not train a model, update weights, modify the default profile, enable real promotion, enable user-facing production, claim production support, add natural language, or release.",
        "",
        "## Mainline Result",
    ]
    keys = [
        "coverage_replay_completed", "wall_clock_hours", "no_model_training", "no_weight_update", "default_profile_unchanged",
        "explicit_opt_in_required", "real_promotion_enabled", "coverage_expansion_successful", "previous_unique_compile_unit_count",
        "new_unique_compile_unit_count", "previous_source_sha256_unique_count", "new_source_sha256_unique_count",
        "repeated_shape_risk_level_before", "repeated_shape_risk_level_after", "replay_16_worker_passed",
        "replay_workers_requested", "replay_workers_used", "replay_downgraded", "default_blocking_passed",
        "malformed_opt_in_blocking_passed", "function_opt_in_success_rate", "array_opt_in_success_rate",
        "function_array_opt_in_success_rate", "structured_recursion_opt_in_success_rate", "mixed_opt_in_success_rate",
        "opt_out_rollback_passed", "real_compiler_invocations", "unique_compile_unit_count", "source_sha256_unique_count",
        "shape_signature_unique_count", "trace_pack_replayable", "ready_for_controlled_opt_in_support_candidate_review",
        "production_function_support_completed", "production_array_support_completed", "production_recursion_support_completed",
        "recommended_claim_level", "blocking_issues", "required_next_run",
    ]
    for key in keys:
        lines.append(f"- {key}: {readiness.get(key)}")
    lines.extend(["", "## Still Not Proven"])
    lines.extend(f"- {item}" for item in STILL_NOT_PROVEN)
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "mainline_conclusion.json").write_text(json.dumps({"readiness": readiness}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--args-json", default="")
    for name in ["records-root", "docs-root", "source-records-v1-0-5-1", "source-records-v1-0-5-2", "source-records-v1-0-6", "source-records-v1-0-6-1", "source-records-v1-0-7", "source-records-v1-0-7-1"]:
        p.add_argument(f"--{name}", default="")
    p.add_argument("--output-records", default="records/v1_0_7_2_coverage_replay")
    p.add_argument("--profile-name", default="staged_opt_in_function_array_recursion_v1_0_7")
    for name in ["coverage-expansion", "replay-concurrency-repair", "no-model-training", "no-weight-update", "explicit-opt-in-required", "forbid-default-profile-change", "forbid-default-bridge-leak", "forbid-real-promotion", "forbid-user-facing-enable", "forbid-release", "accounting-lock", "require-shape-signature-tracking", "require-all-categories", "require-v1-0-6-adapter-reuse", "require-atomic-policy-bridge", "require-extended-ir-path", "require-extended-emitter", "forbid-template-bypass", "forbid-marker-ir-direct-compile", "forbid-summary-only-validation", "run-default-blocking-audit", "run-regression-guard", "run-opt-in-rollback", "run-16-worker-replay", "run-trace-pack-builder", "run-claim-boundary-review", "run-architecture-charter-guard", "progress"]:
        p.add_argument(f"--{name}", type=_bool, default=True)
    p.add_argument("--wall-clock-min-hours", type=float, default=4.0)
    p.add_argument("--max-runtime-hours", type=float, default=4.0)
    p.add_argument("--hard-stop-hours", type=float, default=4.5)
    p.add_argument("--workers", type=int, default=16)
    p.add_argument("--compiler-workers", type=int, default=16)
    p.add_argument("--replay-workers", type=int, default=16)
    p.add_argument("--trace-writer-mode", default="sharded")
    p.add_argument("--temp-dir-mode", default="per_sample")
    p.add_argument("--target-real-validation-events", type=int, default=165000)
    p.add_argument("--minimum-real-validation-events", type=int, default=80000)
    p.add_argument("--minimum-real-compiler-invocations", type=int, default=50000)
    p.add_argument("--default-blocking-target", type=int, default=10000)
    p.add_argument("--malformed-opt-in-blocking-target", type=int, default=5000)
    p.add_argument("--arithmetic-target", type=int, default=15000)
    p.add_argument("--function-target", type=int, default=25000)
    p.add_argument("--array-target", type=int, default=25000)
    p.add_argument("--function-array-target", type=int, default=25000)
    p.add_argument("--recursion-target", type=int, default=15000)
    p.add_argument("--mixed-target", type=int, default=30000)
    p.add_argument("--opt-out-rollback-target", type=int, default=10000)
    p.add_argument("--post-rollback-default-blocking-target", type=int, default=5000)
    p.add_argument("--replay-samples", type=int, default=8000)
    p.add_argument("--replay-minimum-required", type=int, default=5000)
    p.add_argument("--minimum-unique-compile-units", type=int, default=12000)
    p.add_argument("--target-unique-compile-units", type=int, default=20000)
    p.add_argument("--minimum-source-sha256-unique", type=int, default=12000)
    p.add_argument("--target-source-sha256-unique", type=int, default=20000)
    p.add_argument("--seed", default="210")
    args = p.parse_args()
    if args.args_json:
        payload = json.loads(Path(args.args_json).read_text(encoding="utf-8-sig"))
        for key, value in payload.items():
            setattr(args, key.replace("-", "_"), value)
    return args


def _checkpoint(out: Path, phase: str) -> None:
    payload = {"phase": phase}
    with (out / "coverage_replay_runner_checkpoints.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    _safe_print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return value.lower() in {"1", "true", "yes", "on"}


def _first_seed(value: str) -> int:
    return int(str(value).split(",", 1)[0])


def _safe_print(text: str) -> None:
    try:
        print(text, flush=True)
    except OSError:
        try:
            sys.stderr.write(text + "\n")
            sys.stderr.flush()
        except OSError:
            pass


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        try:
            out = Path("records/v1_0_7_2_coverage_replay")
            out.mkdir(parents=True, exist_ok=True)
            (out / "coverage_replay_runner_failure.json").write_text(
                json.dumps({"failure_type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        finally:
            raise
