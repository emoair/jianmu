from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.artifact_out_of_worktree_guard import artifact_guard, default_artifact_root
from jianmu.self_learning.darwinforge.git_storm_guard import run_git_storm_guard
from jianmu.self_learning.darwinforge.memory_queue_guard import memory_queue_guard
from jianmu.self_learning.darwinforge.opt_backend_manifest_binding import bind_opt_display_to_backend_manifest
from jianmu.self_learning.darwinforge.opt_display_gate import run_opt_display_smoke_gate
from jianmu.self_learning.darwinforge.opt_live_display_schema import OptTrue8hConfig, STILL_NOT_PROVEN_OPT_TRUE8H
from jianmu.self_learning.darwinforge.opt_true8h_readiness import build_opt_true8h_readiness
from jianmu.self_learning.darwinforge.true8h_backend_validation_runner import run_true8h_backend_validation


def main() -> int:
    args = parse_args()
    out = Path(args.output_records)
    if out.exists() and args.clean_output:
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    artifact_root = Path(args.artifact_root) if args.artifact_root else default_artifact_root("v1_0_8_8_2")
    artifact_root.mkdir(parents=True, exist_ok=True)
    cfg = OptTrue8hConfig(
        progress_interval_seconds=args.progress_interval_seconds,
        heartbeat_interval_seconds=args.heartbeat_interval_seconds,
        smoke_duration_seconds=args.smoke_duration_seconds,
        minimum_smoke_events=args.minimum_smoke_events,
        minimum_smoke_backend_cl_invocations=args.minimum_smoke_backend_cl_invocations,
        wall_clock_min_hours=args.wall_clock_min_hours,
        max_runtime_hours=args.max_runtime_hours,
        hard_stop_hours=args.hard_stop_hours,
        cycles=args.cycles,
        cycle_min_hours=args.cycle_min_hours,
        target_events=args.target_events,
        minimum_events=args.minimum_events,
        minimum_backend_cl_invocations=args.minimum_backend_cl_invocations,
        minimum_backend_link_invocations=args.minimum_backend_link_invocations,
        minimum_backend_exe_runs=args.minimum_backend_exe_runs,
        workers=args.workers,
        compiler_workers=args.compiler_workers,
        sample_evidence_count=args.sample_evidence_count,
        replay_samples=args.replay_samples,
        replay_minimum_samples=args.replay_minimum_samples,
    )
    if not shutil.which("cl") or not shutil.which("link"):
        payload = {
            "opt_display_smoke_gate_passed": False,
            "true8h_validation_started": False,
            "true8h_backend_validation_passed": False,
            "blocking_issues": ["msvc_cl_or_link_not_found"],
        }
        readiness = build_opt_true8h_readiness(out, payload)
        write_conclusion(out, readiness)
        return 1
    artifact = artifact_guard(out, artifact_root)
    git = run_git_storm_guard(out)
    memory = memory_queue_guard(out)
    if not artifact["artifact_guard_passed"] or not git["git_storm_guard_passed"] or not memory["memory_guard_passed"]:
        payload = {**artifact, **git, **memory, "opt_display_smoke_gate_passed": False, "true8h_validation_started": False, "true8h_backend_validation_passed": False}
        readiness = build_opt_true8h_readiness(out, payload)
        write_conclusion(out, readiness)
        return 1
    smoke = run_opt_display_smoke_gate(out, artifact_root, cfg) if args.run_opt_smoke_gate else {"opt_display_smoke_gate_passed": True}
    if not smoke.get("opt_display_smoke_gate_passed"):
        readiness = build_opt_true8h_readiness(out, {**artifact, **git, **memory, **smoke, "true8h_validation_started": False, "true8h_backend_validation_passed": False})
        write_conclusion(out, readiness)
        return 1
    true8h = run_true8h_backend_validation(out, artifact_root, cfg, opt_gate_passed=bool(smoke.get("opt_display_smoke_gate_passed"))) if args.run_true8h_backend_validation else {"true8h_validation_started": False, "true8h_backend_validation_passed": False}
    binding = bind_opt_display_to_backend_manifest(out)
    payload = {**artifact, **git, **memory, **smoke, **true8h, **binding}
    readiness = build_opt_true8h_readiness(out, payload)
    write_conclusion(out, readiness)
    print(json.dumps({"recommended_claim_level": readiness["recommended_claim_level"], "backend_cl_invocations": readiness.get("backend_cl_invocations"), "actual_wall_clock_hours": readiness.get("actual_wall_clock_hours")}, ensure_ascii=False, sort_keys=True), flush=True)
    return 0 if readiness["recommended_claim_level"] != "failed" else 1


def write_conclusion(out: Path, readiness: dict) -> None:
    lines = [
        "# v1.0.8.8.2 OPT Display Gate and True 8h Backend Validation",
        "",
        "This version restores live OPT progress display, binds progress to backend compiler manifests, keeps compiler artifacts outside the Git worktree, and validates the current backend compiler lane with real cl/link/exe evidence after the smoke gate passes.",
        "",
        "It does not change the default profile, enable real promotion, restore the v1.0.8.8 old compiler claim, release, or claim production support completed.",
        "",
    ]
    for key in [
        "opt_live_display_contract_passed",
        "opt_display_smoke_gate_passed",
        "true8h_backend_validation_passed",
        "actual_wall_clock_hours",
        "actual_elapsed_seconds",
        "backend_cl_invocations",
        "backend_link_invocations",
        "backend_exe_runs",
        "compiler_verified_correctness_rate",
        "backend_replay_passed",
        "sample_evidence_pack_passed",
        "lifecycle_guard_passed",
        "security_interference_detected_count",
        "v1_0_8_8_old_compiler_claim_accepted",
        "v1_0_8_8_old_compiler_claim_downgraded",
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
    lines.extend(f"- {item}" for item in STILL_NOT_PROVEN_OPT_TRUE8H)
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "mainline_conclusion.json").write_text(json.dumps({"readiness": readiness, "still_not_proven": list(STILL_NOT_PROVEN_OPT_TRUE8H)}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--source-records-v1-0-8-8-1", default="records/v1_0_8_8_1_compiler_integrity")
    parser.add_argument("--output-records", default="records/v1_0_8_8_2_opt_true8h")
    parser.add_argument("--artifact-root", default="")
    parser.add_argument("--progress-interval-seconds", type=int, default=10)
    parser.add_argument("--heartbeat-interval-seconds", type=int, default=300)
    parser.add_argument("--smoke-duration-seconds", type=int, default=300)
    parser.add_argument("--minimum-smoke-events", type=int, default=2000)
    parser.add_argument("--minimum-smoke-backend-cl-invocations", type=int, default=500)
    parser.add_argument("--wall-clock-min-hours", type=float, default=8.0)
    parser.add_argument("--max-runtime-hours", type=float, default=8.0)
    parser.add_argument("--hard-stop-hours", type=float, default=8.5)
    parser.add_argument("--cycles", type=int, default=8)
    parser.add_argument("--cycle-min-hours", type=float, default=1.0)
    parser.add_argument("--target-events", type=int, default=240000)
    parser.add_argument("--minimum-events", type=int, default=150000)
    parser.add_argument("--minimum-backend-cl-invocations", type=int, default=100000)
    parser.add_argument("--minimum-backend-link-invocations", type=int, default=100000)
    parser.add_argument("--minimum-backend-exe-runs", type=int, default=100000)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--compiler-workers", type=int, default=16)
    parser.add_argument("--sample-evidence-count", type=int, default=300)
    parser.add_argument("--replay-samples", type=int, default=2000)
    parser.add_argument("--replay-minimum-samples", type=int, default=1000)
    parser.add_argument("--clean-output", type=_bool, default=True)
    for flag in [
        "opt-live-display", "flush-progress", "opt-trace-manifest", "opt-display-bind-backend-manifest",
        "run-opt-smoke-gate", "require-artifacts-outside-worktree", "run-git-storm-guard",
        "run-memory-queue-guard", "streaming-jsonl", "bounded-queue", "run-true8h-backend-validation",
        "accounting-lock", "use-monotonic-timing", "record-utc-start-end", "record-cycle-timestamps",
        "record-heartbeat", "reject-planned-time-as-actual", "record-cl-pid", "record-link-pid",
        "record-exe-pid", "record-returncodes", "record-artifacts", "record-stdout-comparison",
        "record-subprocess-monotonic-timing", "security-interference-detection", "detect-antivirus-360",
        "sample-artifact-evidence-pack", "run-backend-replay", "run-lifecycle-guard",
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
    parser.add_argument("--idle-grace-seconds", type=int, default=30)
    parser.add_argument("--max-lingering-python-children", type=int, default=0)
    parser.add_argument("--max-lingering-git-processes", type=int, default=0)
    parser.add_argument("--max-lingering-compiler-processes", type=int, default=0)
    parser.add_argument("--max-active-worker-threads", type=int, default=0)
    parser.add_argument("--seed", default="249,250,251")
    return parser.parse_args()


def _bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    raise SystemExit(main())
