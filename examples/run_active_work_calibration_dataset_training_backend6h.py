from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.active_work_threshold_calibrator import calibrate_active_work_threshold
from jianmu.self_learning.darwinforge.backend6h_validation_runner import run_backend6h_validation
from jianmu.self_learning.darwinforge.dataset_artifact_hygiene_guard import run_dataset_artifact_hygiene_guard
from jianmu.self_learning.darwinforge.dataset_backend6h_readiness import build_dataset_backend6h_readiness
from jianmu.self_learning.darwinforge.dataset_mirror_feedback import build_mirror_dataset_feedback
from jianmu.self_learning.darwinforge.dataset_redqueen_scheduler import build_redqueen_dataset_schedule
from jianmu.self_learning.darwinforge.incremental_curriculum_dataset_builder import build_incremental_curriculum_dataset
from jianmu.self_learning.darwinforge.incremental_dataset_schema import IncrementalDatasetConfig
from jianmu.self_learning.darwinforge.opt_active_work_schema import STILL_NOT_PROVEN_OPT_ACTIVE_WORK
from jianmu.self_learning.darwinforge.trace_shard_size_cap import audit_trace_shard_size_cap
from jianmu.self_learning.darwinforge.train_heldout_split_guard import run_train_heldout_split_guard


STILL_NOT_PROVEN = (
    "production function support completed",
    "production array support completed",
    "production recursion support completed",
    "RedQueen autonomous governance completed",
    "production readiness",
    "formal Turing completeness proof",
    "solved program synthesis",
    "natural language layer completed",
    "pure validation on the newly trained incremental dataset",
)


def main() -> int:
    args = parse_args()
    out = Path(args.output_records)
    if out.exists() and args.clean_output:
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    dataset_artifact_root = Path(os.path.expandvars(args.dataset_artifact_root))
    backend_artifact_root = Path(os.environ.get("JIANMU_COMPILER_INTEGRITY_ARTIFACT_ROOT", Path(os.environ.get("TEMP", ".")) / "jianmu_compiler_integrity_artifacts")) / "v1_0_8_8_4"
    calibration = calibrate_active_work_threshold(args.source_records_v1_0_8_8_3, out)
    conservative = max(args.minimum_backend_cl_invocations, int(calibration.get("conservative_minimum_6h_backend_invocations", 0) or 0))
    target = max(args.target_backend_cl_invocations, int(calibration.get("target_6h_backend_invocations", 0) or 0))
    redqueen = build_redqueen_dataset_schedule(out, calibration)
    mirror = build_mirror_dataset_feedback(out, redqueen)
    dataset_cfg = IncrementalDatasetConfig(
        target_dataset_samples=args.target_dataset_samples,
        minimum_dataset_samples=args.minimum_dataset_samples,
        train_ratio=args.train_ratio,
        heldout_ratio=args.heldout_ratio,
        replay_ratio=args.replay_ratio,
        negative_boundary_ratio=args.negative_boundary_ratio,
        evidence_count=args.sample_evidence_count,
    )
    dataset = build_incremental_curriculum_dataset(out, dataset_artifact_root, dataset_cfg, redqueen, mirror)
    split = run_train_heldout_split_guard(out, out / "dataset_manifest_shards")
    repo = run_dataset_artifact_hygiene_guard(out, dataset_artifact_root)
    backend = run_backend6h_validation(
        out,
        backend_artifact_root,
        wall_clock_min_hours=args.wall_clock_min_hours,
        hard_stop_hours=args.hard_stop_hours,
        cycles=args.cycles,
        compiler_workers=args.compiler_workers,
        progress_interval_seconds=args.progress_interval_seconds,
        heartbeat_interval_seconds=args.heartbeat_interval_seconds,
        minimum_backend_cl_invocations=conservative,
        minimum_backend_link_invocations=max(args.minimum_backend_link_invocations, conservative),
        minimum_backend_exe_runs=max(args.minimum_backend_exe_runs, conservative),
        target_backend_cl_invocations=target,
        required_backend_active_window_ratio=args.require_backend_active_window_ratio,
        dataset_summary=dataset,
        split_guard=split,
        max_trace_shard_size_bytes=args.max_trace_shard_size_bytes,
        hard_fail_trace_shard_size_bytes=args.hard_fail_trace_shard_size_bytes,
    )
    shard = audit_trace_shard_size_cap(out, output_records=out, max_trace_shard_size_bytes=args.max_trace_shard_size_bytes, hard_fail_threshold_bytes=args.hard_fail_trace_shard_size_bytes)
    payload = {**calibration, **dataset, **split, **redqueen, **mirror, **repo, **backend, **shard}
    readiness = build_dataset_backend6h_readiness(out, payload)
    write_conclusion(out, readiness)
    print(json.dumps({"recommended_claim_level": readiness["recommended_claim_level"], "backend_cl_invocations": readiness.get("backend_cl_invocations"), "actual_wall_clock_hours": readiness.get("actual_wall_clock_hours")}, ensure_ascii=False, sort_keys=True), flush=True)
    return 0 if readiness["recommended_claim_level"] in {"active_work_calibrated_dataset_training_backend6h_positive", "dataset_training_positive_backend6h_partial"} else 1


def write_conclusion(out: Path, readiness: dict) -> None:
    lines = [
        "# v1.0.8.8.4 Active Work Calibration, Incremental Dataset Training, and 6h Backend Validation",
        "",
        "This version calibrates active backend thresholds from observed MSVC throughput, builds an incremental curriculum dataset, separates train/heldout/replay/negative lanes, and runs a true 6-hour backend compiler validation.",
        "",
        "It does not change the default profile, enable real promotion, release, claim production support completed, claim RedQueen autonomous governance completed, or treat training-set self-score as heldout validation.",
        "",
    ]
    for key in [
        "threshold_calibration_passed",
        "observed_backend_rate_per_second",
        "expected_6h_backend_invocations",
        "conservative_minimum_6h_backend_invocations",
        "fixed_20k_45min_threshold_rejected",
        "dataset_training_completed",
        "total_dataset_samples",
        "train_samples",
        "heldout_samples",
        "replay_samples",
        "negative_boundary_samples",
        "categories_covered",
        "no_model_weight_update",
        "dataset_artifacts_outside_worktree",
        "split_guard_passed",
        "leakage_detected",
        "redqueen_dataset_scheduler_passed",
        "mirror_feedback_passed",
        "backend6h_validation_completed",
        "actual_wall_clock_hours",
        "actual_elapsed_seconds",
        "cycles_completed",
        "backend_cl_invocations",
        "backend_link_invocations",
        "backend_exe_runs",
        "backend_active_window_ratio",
        "idle_padding_detected",
        "compiler_verified_correctness_rate",
        "wrong_stdout_count",
        "timeout_count",
        "permission_error_count",
        "cleanup_failure_count",
        "train_heldout_leakage_detected",
        "dataset_evidence_pack_passed",
        "repo_hygiene_guard_passed",
        "trace_shard_size_cap_passed",
        "largest_shard_bytes",
        "memory_guard_passed",
        "lifecycle_guard_passed",
        "default_profile_unchanged",
        "real_promotion_enabled",
        "production_function_support_completed",
        "production_array_support_completed",
        "production_recursion_support_completed",
        "redqueen_autonomous_governance_completed",
        "ready_for_official_release",
        "recommended_claim_level",
        "blocking_issues",
        "required_next_run",
    ]:
        lines.append(f"- {key}: `{readiness.get(key)}`")
    lines.extend(["", "## Still Not Proven", ""])
    lines.extend(f"- {item}" for item in STILL_NOT_PROVEN)
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "mainline_conclusion.json").write_text(json.dumps({"readiness": readiness, "still_not_proven": list(STILL_NOT_PROVEN), "prior_still_not_proven": list(STILL_NOT_PROVEN_OPT_ACTIVE_WORK)}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--source-records-v1-0-8-8-3", default="records/v1_0_8_8_3_opt_git_repair")
    parser.add_argument("--output-records", default="records/v1_0_8_8_4_dataset_backend6h")
    parser.add_argument("--dataset-artifact-root", default="%TEMP%/jianmu_dataset_artifacts/v1_0_8_8_4")
    parser.add_argument("--target-dataset-samples", type=int, default=500_000)
    parser.add_argument("--minimum-dataset-samples", type=int, default=250_000)
    parser.add_argument("--train-ratio", type=float, default=0.70)
    parser.add_argument("--heldout-ratio", type=float, default=0.15)
    parser.add_argument("--replay-ratio", type=float, default=0.10)
    parser.add_argument("--negative-boundary-ratio", type=float, default=0.05)
    parser.add_argument("--wall-clock-min-hours", type=float, default=6.0)
    parser.add_argument("--max-runtime-hours", type=float, default=6.0)
    parser.add_argument("--hard-stop-hours", type=float, default=6.5)
    parser.add_argument("--cycles", type=int, default=6)
    parser.add_argument("--cycle-min-hours", type=float, default=1.0)
    parser.add_argument("--minimum-backend-cl-invocations", type=int, default=68_000)
    parser.add_argument("--target-backend-cl-invocations", type=int, default=88_000)
    parser.add_argument("--minimum-backend-link-invocations", type=int, default=68_000)
    parser.add_argument("--minimum-backend-exe-runs", type=int, default=68_000)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--compiler-workers", type=int, default=16)
    parser.add_argument("--progress-interval-seconds", type=int, default=10)
    parser.add_argument("--heartbeat-interval-seconds", type=int, default=300)
    parser.add_argument("--require-backend-active-window-ratio", type=float, default=0.90)
    parser.add_argument("--sample-evidence-count", type=int, default=500)
    parser.add_argument("--max-trace-shard-size-bytes", type=int, default=44_000_000)
    parser.add_argument("--hard-fail-trace-shard-size-bytes", type=int, default=50_000_000)
    parser.add_argument("--clean-output", type=_bool, default=True)
    for flag in [
        "calibrate-active-work-threshold", "reject-fixed-20k-45min-threshold", "incremental-dataset-training",
        "require-dataset-artifacts-outside-worktree", "run-train-heldout-split-guard", "run-redqueen-dataset-scheduler",
        "run-mirror-dataset-feedback", "run-backend6h-validation", "accounting-lock", "forbid-idle-padding",
        "use-monotonic-timing", "record-utc-start-end", "record-heartbeat", "record-cl-pid", "record-link-pid",
        "record-exe-pid", "record-returncodes", "record-artifacts", "record-stdout-comparison",
        "security-interference-detection", "detect-antivirus-360", "sample-artifact-evidence-pack",
        "run-repo-hygiene-guard", "run-trace-shard-size-cap", "run-memory-queue-guard", "run-lifecycle-guard",
        "allow-main-thread-only", "no-model-training", "no-weight-update", "explicit-opt-in-required",
        "forbid-default-profile-change", "forbid-real-promotion", "forbid-release", "require-v1-0-6-adapter-reuse",
        "require-atomic-policy-bridge", "require-extended-ir-path", "require-extended-emitter",
        "forbid-template-bypass", "forbid-marker-ir-direct-compile", "forbid-summary-only-validation",
        "run-claim-boundary-review", "run-architecture-charter-guard", "progress",
    ]:
        parser.add_argument(f"--{flag}", type=_bool, default=True)
    parser.add_argument("--trace-writer-mode", default="sharded")
    parser.add_argument("--temp-dir-mode", default="per_sample")
    parser.add_argument("--idle-grace-seconds", type=float, default=30.0)
    parser.add_argument("--max-lingering-python-children", type=int, default=0)
    parser.add_argument("--max-lingering-git-processes", type=int, default=0)
    parser.add_argument("--max-lingering-compiler-processes", type=int, default=0)
    parser.add_argument("--max-active-worker-threads", type=int, default=0)
    parser.add_argument("--seed", default="255,256,257")
    return parser.parse_args()


def _bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    raise SystemExit(main())
