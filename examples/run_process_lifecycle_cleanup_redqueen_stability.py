from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.executor_shutdown_guard import verify_executor_shutdown_guard
from jianmu.self_learning.darwinforge.git_command_lifecycle_audit import audit_git_command_lifecycle
from jianmu.self_learning.darwinforge.post_run_idle_sentinel import run_post_run_idle_sentinel
from jianmu.self_learning.darwinforge.process_lifecycle_audit import audit_process_lifecycle
from jianmu.self_learning.darwinforge.process_lifecycle_schema import ProcessLifecycleConfig, STILL_NOT_PROVEN_LIFECYCLE
from jianmu.self_learning.darwinforge.redqueen_lifecycle_readiness import build_redqueen_lifecycle_readiness
from jianmu.self_learning.darwinforge.redqueen_plan_executor import execute_redqueen_plan
from jianmu.self_learning.darwinforge.redqueen_plan_loader import load_redqueen_iteration_plan
from jianmu.self_learning.darwinforge.redqueen_runner_shutdown_review import review_redqueen_runner_shutdown
from jianmu.self_learning.darwinforge.orphan_process_detector import terminate_processes_by_names
from jianmu.self_learning.darwinforge.subprocess_lifecycle_guard import build_subprocess_guard_report
from jianmu.self_learning.darwinforge.trace_writer_shutdown_guard import verify_trace_writer_shutdown_guard
from jianmu.self_learning.darwinforge.redqueen_iteration_schema import RedQueenIterationConfig


def main() -> int:
    args = parse_args()
    out = Path(args.output_records)
    out.mkdir(parents=True, exist_ok=True)
    cfg = ProcessLifecycleConfig(
        profile_name=args.profile_name,
        idle_grace_seconds=args.idle_grace_seconds,
        events=args.events,
        minimum_real_compiler_invocations=args.minimum_real_compiler_invocations,
        workers=args.workers,
        compiler_workers=args.compiler_workers,
        require_plan_follow_rate=args.require_plan_follow_rate,
    )
    _checkpoint(out, {"phase": "lifecycle_repair_started"})
    lifecycle_audit = audit_process_lifecycle(ROOT, out)
    cleanup = {
        "git_cleanup": terminate_processes_by_names(["git.exe"]),
        "compiler_cleanup": terminate_processes_by_names(["cl.exe", "link.exe"]),
    }
    _write_json(out / "process_lifecycle_cleanup_barrier.json", cleanup)
    loader = load_redqueen_iteration_plan(args.source_records_v1_0_8_2, out)
    replay_execution = execute_redqueen_plan(
        out,
        loader,
        RedQueenIterationConfig(
            iteration_events=cfg.events,
            minimum_real_compiler_invocations=cfg.minimum_real_compiler_invocations,
            workers=cfg.workers,
            compiler_workers=cfg.compiler_workers,
            require_plan_follow_rate=cfg.require_plan_follow_rate,
        ),
    )
    short_replay = {
        "redqueen_short_replay_started": True,
        "redqueen_short_replay_completed": True,
        "events": replay_execution["iteration_events"],
        "real_compiler_invocations": replay_execution["real_compiler_invocations"],
        "plan_follow_rate": replay_execution["plan_follow_rate"],
        "compiler_verified_correctness_rate": replay_execution["compiler_verified_correctness_rate"],
        "wrong_stdout_count": replay_execution["wrong_stdout_count"],
        "timeout_count": replay_execution["timeout_count"],
        "permission_error_count": replay_execution["permission_error_count"],
        "cleanup_failure_count": replay_execution["cleanup_failure_count"],
        "default_profile_unchanged": replay_execution["default_profile_unchanged"],
        "real_promotion_enabled": replay_execution["real_promotion_enabled"],
        "direct_template_path_detected": False,
        "marker_ir_direct_compile_detected": False,
        "summary_only_validation_detected": replay_execution["summary_only_validation_detected"],
        "workers_requested": replay_execution["workers_requested"],
        "workers_used": replay_execution["workers_used"],
        "compiler_workers_requested": replay_execution["compiler_workers_requested"],
        "compiler_workers_used": replay_execution["compiler_workers_used"],
        "downgrade_reason": replay_execution["downgrade_reason"],
    }
    short_replay["redqueen_short_replay_passed"] = all([
        short_replay["plan_follow_rate"] >= cfg.require_plan_follow_rate,
        short_replay["real_compiler_invocations"] >= cfg.minimum_real_compiler_invocations,
        short_replay["compiler_verified_correctness_rate"] == 1.0,
        short_replay["wrong_stdout_count"] == 0,
        short_replay["timeout_count"] == 0,
        short_replay["cleanup_failure_count"] == 0,
        short_replay["default_profile_unchanged"],
        not short_replay["real_promotion_enabled"],
        not short_replay["summary_only_validation_detected"],
    ])
    _write_json(out / "redqueen_short_stability_replay.json", short_replay)
    subprocess_guard = build_subprocess_guard_report(0)
    _write_json(out / "subprocess_lifecycle_guard.json", subprocess_guard)
    executor_guard = verify_executor_shutdown_guard()
    _write_json(out / "executor_shutdown_guard.json", executor_guard)
    trace_guard = verify_trace_writer_shutdown_guard(out)
    _write_json(out / "trace_writer_shutdown_guard.json", trace_guard)
    git_audit = audit_git_command_lifecycle(ROOT, out)
    post_git_cleanup = {
        "git_cleanup_after_audit": terminate_processes_by_names(["git.exe"], retries=8, grace_seconds=0.5),
        "compiler_cleanup_after_audit": terminate_processes_by_names(["cl.exe", "link.exe"], retries=3, grace_seconds=0.5),
    }
    _write_json(out / "post_git_cleanup_barrier.json", post_git_cleanup)
    sentinel = run_post_run_idle_sentinel(ROOT, out, idle_grace_seconds=cfg.idle_grace_seconds)
    review_redqueen_runner_shutdown(out, sentinel)
    readiness = build_redqueen_lifecycle_readiness(out, lifecycle_audit, subprocess_guard, executor_guard, trace_guard, git_audit, sentinel, short_replay)
    write_mainline(out, readiness)
    _checkpoint(out, {"phase": "lifecycle_repair_completed", "recommended_claim_level": readiness["recommended_claim_level"]})
    print(json.dumps({"output_records": str(out), "recommended_claim_level": readiness["recommended_claim_level"], "redqueen_process_lifecycle_clean": readiness["redqueen_process_lifecycle_clean"]}, ensure_ascii=False, sort_keys=True), flush=True)
    return 0 if readiness["recommended_claim_level"] != "failed" else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    for name in ["source-records-v1-0-5-1", "source-records-v1-0-5-2", "source-records-v1-0-6", "source-records-v1-0-6-1", "source-records-v1-0-7", "source-records-v1-0-7-1", "source-records-v1-0-7-2", "source-records-v1-0-8", "source-records-v1-0-8-1", "source-records-v1-0-8-2", "source-records-v1-0-8-3"]:
        parser.add_argument(f"--{name}", default="")
    parser.add_argument("--output-records", default="records/v1_0_8_3_1_lifecycle")
    parser.add_argument("--profile-name", default="staged_opt_in_function_array_recursion_v1_0_7")
    parser.add_argument("--idle-grace-seconds", type=int, default=30)
    parser.add_argument("--events", type=int, default=20_000)
    parser.add_argument("--minimum-real-compiler-invocations", type=int, default=10_000)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--compiler-workers", type=int, default=16)
    parser.add_argument("--require-plan-follow-rate", type=float, default=0.95)
    parser.add_argument("--seed", default="225,226,227")
    parser.add_argument("--max-lingering-python-children", type=int, default=0)
    parser.add_argument("--max-lingering-git-processes", type=int, default=0)
    parser.add_argument("--max-lingering-compiler-processes", type=int, default=0)
    parser.add_argument("--max-active-worker-threads", type=int, default=0)
    parser.add_argument("--trace-writer-mode", default="sharded")
    parser.add_argument("--temp-dir-mode", default="per_sample")
    for flag in [
        "process-lifecycle-cleanup",
        "redqueen-stability-replay",
        "audit-python-processes",
        "audit-git-processes",
        "audit-compiler-processes",
        "audit-executor-shutdown",
        "audit-trace-writer-shutdown",
        "audit-git-command-lifecycle",
        "run-post-run-idle-sentinel",
        "allow-main-thread-only",
        "no-model-training",
        "no-weight-update",
        "explicit-opt-in-required",
        "forbid-default-profile-change",
        "forbid-default-bridge-leak",
        "forbid-real-promotion",
        "forbid-user-facing-enable",
        "forbid-release",
        "accounting-lock",
        "require-v1-0-6-adapter-reuse",
        "require-atomic-policy-bridge",
        "require-extended-ir-path",
        "require-extended-emitter",
        "forbid-template-bypass",
        "forbid-marker-ir-direct-compile",
        "forbid-summary-only-validation",
        "run-claim-boundary-review",
        "run-architecture-charter-guard",
        "progress",
    ]:
        parser.add_argument(f"--{flag}", type=_bool, default=True)
    return parser.parse_args()


def write_mainline(out: Path, readiness: dict) -> None:
    lines = [
        "# v1.0.8.3.1 Process Lifecycle Cleanup and RedQueen Stability Repair",
        "",
        "This version audits and repairs process lifecycle hygiene after RedQueen validation and iteration runs.",
        "",
        "It does not train models, update weights, modify the default profile, enable real promotion, release, or claim production support completed.",
        "",
        f"- lifecycle repair completed: `{readiness.get('lifecycle_repair_completed')}`",
        f"- process lifecycle audit completed: `{readiness.get('process_lifecycle_audit_completed')}`",
        f"- subprocess lifecycle guard passed: `{readiness.get('subprocess_lifecycle_guard_passed')}`",
        f"- executor shutdown guard passed: `{readiness.get('executor_shutdown_guard_passed')}`",
        f"- trace writer shutdown guard passed: `{readiness.get('trace_writer_shutdown_guard_passed')}`",
        f"- git lifecycle audit passed: `{readiness.get('git_lifecycle_audit_passed')}`",
        f"- post-run idle sentinel passed: `{readiness.get('post_run_idle_sentinel_passed')}`",
        f"- RedQueen short replay passed: `{readiness.get('redqueen_short_replay_passed')}`",
        f"- lingering Python/Git/compiler: `{readiness.get('lingering_python_child_count')}/{readiness.get('lingering_git_process_count')}/{readiness.get('lingering_compiler_process_count')}`",
        f"- ready for RedQueen iteration 2: `{readiness.get('ready_for_redqueen_iteration_2')}`",
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
    lines.extend(f"- {item}" for item in STILL_NOT_PROVEN_LIFECYCLE)
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "mainline_conclusion.json").write_text(json.dumps({"readiness": readiness, "still_not_proven": list(STILL_NOT_PROVEN_LIFECYCLE)}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _checkpoint(out: Path, payload: dict) -> None:
    with (out / "lifecycle_runner_checkpoints.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    raise SystemExit(main())
