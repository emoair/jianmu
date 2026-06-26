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

from jianmu.self_learning.darwinforge.active_backend_validation_runner import run_active_backend_validation
from jianmu.self_learning.darwinforge.git_residual_cleanup_guard import run_git_residual_cleanup_guard
from jianmu.self_learning.darwinforge.git_residual_process_audit import audit_git_residual_processes
from jianmu.self_learning.darwinforge.idle_padding_detector import detect_idle_padding
from jianmu.self_learning.darwinforge.opt_active_work_audit import audit_v1_0_8_8_2_active_work
from jianmu.self_learning.darwinforge.opt_active_work_readiness import build_opt_active_work_readiness
from jianmu.self_learning.darwinforge.opt_active_work_schema import OptActiveWorkConfig, STILL_NOT_PROVEN_OPT_ACTIVE_WORK, opt_active_work_rate_contract
from jianmu.self_learning.darwinforge.opt_backend_consistency_audit import audit_opt_backend_consistency, load_jsonl
from jianmu.self_learning.darwinforge.too_perfect_output_detector import detect_too_perfect_output
from jianmu.self_learning.darwinforge.trace_shard_size_cap import audit_trace_shard_size_cap


def main() -> int:
    args = parse_args()
    out = Path(args.output_records)
    if out.exists() and args.clean_output:
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    artifact_root = Path(os.path.expandvars(args.artifact_root))
    artifact_root.mkdir(parents=True, exist_ok=True)
    config = OptActiveWorkConfig(
        duration_minutes=args.duration_minutes,
        minimum_actual_elapsed_seconds=args.minimum_actual_elapsed_seconds,
        events=args.events,
        minimum_backend_cl_invocations=args.minimum_backend_cl_invocations,
        minimum_backend_link_invocations=args.minimum_backend_link_invocations,
        minimum_backend_exe_runs=args.minimum_backend_exe_runs,
        workers=args.workers,
        compiler_workers=args.compiler_workers,
        progress_interval_seconds=args.progress_interval_seconds,
        heartbeat_interval_seconds=args.heartbeat_interval_seconds,
        required_backend_active_window_ratio=args.require_backend_active_window_ratio,
        max_trace_shard_size_bytes=args.max_trace_shard_size_bytes,
        trace_hard_fail_threshold_bytes=args.hard_fail_trace_shard_size_bytes,
    )
    active_audit = audit_v1_0_8_8_2_active_work(args.source_records_v1_0_8_8_2, out)
    rate_contract = opt_active_work_rate_contract()
    (out / "opt_active_work_rate_contract.json").write_text(json.dumps(rate_contract, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    old_summary = _read_json(Path(args.source_records_v1_0_8_8_2) / "true8h_backend_validation_summary.json")
    old_progress = load_jsonl(Path(args.source_records_v1_0_8_8_2) / "opt_progress_trace.jsonl")
    old_too_perfect = detect_too_perfect_output(old_summary, old_progress, output_records=out)
    git_audit = audit_git_residual_processes(out)
    git_cleanup = run_git_residual_cleanup_guard(out, idle_wait_seconds=args.idle_grace_seconds)
    active = run_active_backend_validation(out, artifact_root, config) if args.run_active_backend_validation else {}
    progress_rows = load_jsonl(out / "active_opt_progress_trace.jsonl")
    idle = detect_idle_padding(progress_rows, output_records=out)
    consistency = audit_opt_backend_consistency(out, manifest_path=out / "active_backend_manifest", progress_path=out / "active_opt_progress_trace.jsonl", stdout_path=out / "active_backend_stdout_comparison.jsonl")
    new_too_perfect = detect_too_perfect_output(active, progress_rows, output_records=out)
    shard = audit_trace_shard_size_cap(out, output_records=out, max_trace_shard_size_bytes=config.max_trace_shard_size_bytes, hard_fail_threshold_bytes=config.trace_hard_fail_threshold_bytes)
    payload = {**active_audit, **rate_contract, **idle, **consistency, **new_too_perfect, **git_audit, **git_cleanup, **shard, **active}
    # Keep old-run risk visible without blocking a repaired short validation.
    payload["v1_0_8_8_2_too_perfect_notes"] = old_too_perfect
    readiness = build_opt_active_work_readiness(out, payload)
    write_conclusion(out, readiness)
    print(json.dumps({"recommended_claim_level": readiness["recommended_claim_level"], "backend_cl_invocations": readiness.get("backend_cl_invocations"), "active_ratio": readiness.get("backend_active_window_ratio")}, ensure_ascii=False, sort_keys=True), flush=True)
    return 0 if readiness["recommended_claim_level"] in {"opt_active_work_git_lifecycle_repaired", "opt_active_work_repaired_with_git_notes"} else 1


def write_conclusion(out: Path, readiness: dict) -> None:
    lines = [
        "# v1.0.8.8.3 OPT Active Work Rate and Git Residual Process Repair",
        "",
        "This version audits whether OPT progress reflects active backend compiler work, adds delta/rate/last-active-age display, checks idle padding, audits Git residual processes, enforces trace shard size caps, and runs a short active backend validation.",
        "",
        "It does not rerun 8h, restore the old v1.0.8.8 compiler claim, change the default profile, enable real promotion, release, or claim production support completed.",
        "",
    ]
    for key in [
        "v1_0_8_8_2_active_work_claim_accepted",
        "v1_0_8_8_2_active_work_claim_downgraded",
        "active_work_integrity_status",
        "backend_invocation_time_span_hours",
        "zero_delta_progress_window_count",
        "idle_padding_seconds_detected",
        "backend_work_continued_after_target",
        "opt_active_work_rate_contract_passed",
        "idle_padding_detector_passed",
        "opt_backend_consistency_audit_passed",
        "too_perfect_output_detector_passed",
        "git_residual_audit_passed",
        "git_cleanup_guard_passed",
        "git_processes_after_idle",
        "git_index_lock_detected",
        "git_residual_root_cause",
        "trace_shard_size_cap_passed",
        "oversized_shard_count",
        "largest_shard_bytes",
        "active_backend_validation_passed",
        "actual_elapsed_seconds",
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
    lines.extend(f"- {item}" for item in STILL_NOT_PROVEN_OPT_ACTIVE_WORK)
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "mainline_conclusion.json").write_text(json.dumps({"readiness": readiness, "still_not_proven": list(STILL_NOT_PROVEN_OPT_ACTIVE_WORK)}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--source-records-v1-0-8-8-2", default="records/v1_0_8_8_2_opt_true8h")
    parser.add_argument("--output-records", default="records/v1_0_8_8_3_opt_git_repair")
    parser.add_argument("--artifact-root", default="%TEMP%/jianmu_compiler_integrity_artifacts/v1_0_8_8_3")
    parser.add_argument("--duration-minutes", type=float, default=45.0)
    parser.add_argument("--minimum-actual-elapsed-seconds", type=float, default=2700.0)
    parser.add_argument("--events", type=int, default=40000)
    parser.add_argument("--minimum-backend-cl-invocations", type=int, default=20000)
    parser.add_argument("--minimum-backend-link-invocations", type=int, default=20000)
    parser.add_argument("--minimum-backend-exe-runs", type=int, default=20000)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--compiler-workers", type=int, default=16)
    parser.add_argument("--progress-interval-seconds", type=int, default=10)
    parser.add_argument("--heartbeat-interval-seconds", type=int, default=300)
    parser.add_argument("--require-backend-active-window-ratio", type=float, default=0.90)
    parser.add_argument("--max-trace-shard-size-bytes", type=int, default=44_000_000)
    parser.add_argument("--hard-fail-trace-shard-size-bytes", type=int, default=50_000_000)
    parser.add_argument("--idle-grace-seconds", type=float, default=30.0)
    parser.add_argument("--clean-output", type=_bool, default=True)
    parser.add_argument("--run-active-backend-validation", type=_bool, default=True)
    for flag in [
        "audit-v1-0-8-8-2-active-work", "opt-active-work-rate", "display-backend-delta",
        "display-backend-rate", "display-last-backend-age", "display-idle-windows",
        "display-git-process-count", "run-idle-padding-detector", "run-opt-backend-consistency-audit",
        "run-too-perfect-output-detector", "run-git-residual-process-audit", "run-git-cleanup-guard",
        "run-trace-shard-size-cap", "require-artifacts-outside-worktree", "accounting-lock",
        "forbid-idle-padding", "use-monotonic-timing", "record-utc-start-end", "record-heartbeat",
        "record-cl-pid", "record-link-pid", "record-exe-pid", "record-returncodes",
        "record-artifacts", "record-stdout-comparison", "security-interference-detection",
        "detect-antivirus-360", "run-memory-queue-guard", "run-lifecycle-guard",
        "allow-main-thread-only", "no-model-training", "no-weight-update", "explicit-opt-in-required",
        "forbid-default-profile-change", "forbid-real-promotion", "forbid-release",
        "require-v1-0-6-adapter-reuse", "require-atomic-policy-bridge", "require-extended-ir-path",
        "require-extended-emitter", "forbid-template-bypass", "forbid-marker-ir-direct-compile",
        "forbid-summary-only-validation", "run-claim-boundary-review", "run-architecture-charter-guard",
        "progress",
    ]:
        parser.add_argument(f"--{flag}", type=_bool, default=True)
    parser.add_argument("--trace-writer-mode", default="sharded")
    parser.add_argument("--temp-dir-mode", default="per_sample")
    parser.add_argument("--max-lingering-python-children", type=int, default=0)
    parser.add_argument("--max-lingering-git-processes", type=int, default=0)
    parser.add_argument("--max-lingering-compiler-processes", type=int, default=0)
    parser.add_argument("--max-active-worker-threads", type=int, default=0)
    parser.add_argument("--seed", default="252,253,254")
    return parser.parse_args()


def _bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


if __name__ == "__main__":
    raise SystemExit(main())
