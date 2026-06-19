from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.architecture_finalization_schema import RedQueenBootstrapConfig, STILL_NOT_PROVEN
from jianmu.self_learning.darwinforge.architecture_finalization_self_check import run_architecture_finalization_self_check
from jianmu.self_learning.darwinforge.redqueen_adaptive_review_allocator import allocate_active_review
from jianmu.self_learning.darwinforge.redqueen_governance_dry_run import build_next_validation_plan, run_redqueen_governance_dry_run
from jianmu.self_learning.darwinforge.redqueen_governance_readiness import build_redqueen_governance_readiness
from jianmu.self_learning.darwinforge.redqueen_linear_difficulty_scheduler import build_linear_difficulty_schedule
from jianmu.self_learning.darwinforge.redqueen_metrics_bus import build_redqueen_metrics_bus
from jianmu.self_learning.darwinforge.redqueen_self_governance_policy import build_self_governance_policy
from jianmu.self_learning.darwinforge.support_scope_codepath_alignment import check_support_scope_codepath_alignment


def main() -> int:
    args = parse_args()
    out = Path(args.output_records)
    out.mkdir(parents=True, exist_ok=True)
    config = RedQueenBootstrapConfig(args.profile_name, args.workers, args.compiler_workers, args.dry_run_events)
    _checkpoint(out, {"phase": "architecture_finalization_started"})
    architecture = run_architecture_finalization_self_check(args.records_root, out)
    alignment = check_support_scope_codepath_alignment(args.source_records_v1_0_8, out)
    if not architecture.get("architecture_finalization_passed") or not alignment.get("support_scope_codepath_aligned"):
        metrics = {"metrics_bus_created": False, "metrics_bus_read_only": True, "categories": []}
        allocation = {"active_review_allocator_completed": False}
        schedule = {"difficulty_scheduler_completed": False}
        policy = build_self_governance_policy(out)
        dry_run = {"redqueen_dry_run_completed": False, "redqueen_dry_run_passed": False}
        next_plan = {"next_validation_plan_generated": False}
    else:
        metrics = build_redqueen_metrics_bus(args.records_root, out)
        allocation = allocate_active_review(out, metrics)
        schedule = build_linear_difficulty_schedule(out, metrics)
        policy = build_self_governance_policy(out)
        dry_run = run_redqueen_governance_dry_run(
            out,
            metrics,
            allocation,
            schedule,
            events=config.dry_run_events,
            workers=config.workers,
            compiler_workers=config.compiler_workers,
        )
        next_plan = build_next_validation_plan(out, allocation, schedule)
    readiness = build_redqueen_governance_readiness(out, architecture, alignment, metrics, allocation, schedule, policy, dry_run, next_plan)
    write_mainline(out, readiness)
    _checkpoint(out, {"phase": "redqueen_readiness_completed", "recommended_claim_level": readiness["recommended_claim_level"]})
    print(json.dumps({"output_records": str(out), "recommended_claim_level": readiness["recommended_claim_level"], "redqueen_governance_bootstrap_ready": readiness["redqueen_governance_bootstrap_ready"]}, ensure_ascii=False, sort_keys=True), flush=True)
    return 0 if readiness["recommended_claim_level"] != "failed" else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    for name in ["source-records-v1-0-5-1", "source-records-v1-0-5-2", "source-records-v1-0-6", "source-records-v1-0-6-1", "source-records-v1-0-7", "source-records-v1-0-7-1", "source-records-v1-0-7-2", "source-records-v1-0-8", "source-records-v1-0-8-1"]:
        parser.add_argument(f"--{name}", default="")
    parser.add_argument("--output-records", default="records/v1_0_8_2_redqueen_bootstrap")
    parser.add_argument("--profile-name", default="staged_opt_in_function_array_recursion_v1_0_7")
    parser.add_argument("--dry-run-events", type=int, default=20_000)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--compiler-workers", type=int, default=16)
    parser.add_argument("--seed", default="219,220,221")
    parser.add_argument("--progress", type=_bool, default=False)
    for flag in [
        "architecture-finalization-self-check",
        "redqueen-governance-bootstrap",
        "no-model-training",
        "no-weight-update",
        "explicit-opt-in-required",
        "forbid-default-profile-change",
        "forbid-default-bridge-leak",
        "forbid-real-promotion",
        "forbid-user-facing-enable",
        "forbid-release",
        "run-support-scope-codepath-alignment",
        "build-redqueen-metrics-bus",
        "run-active-review-allocator",
        "run-linear-difficulty-scheduler",
        "run-self-governance-policy",
        "run-redqueen-dry-run",
        "accounting-lock",
        "require-v1-0-6-adapter-reuse",
        "require-atomic-policy-bridge",
        "require-extended-ir-path",
        "require-extended-emitter",
        "forbid-template-bypass",
        "forbid-marker-ir-direct-compile",
        "forbid-summary-only-validation",
        "build-next-validation-plan",
        "run-claim-boundary-review",
        "run-architecture-charter-guard",
    ]:
        parser.add_argument(f"--{flag}", type=_bool, default=True)
    parser.add_argument("--trace-writer-mode", default="sharded")
    parser.add_argument("--temp-dir-mode", default="per_sample")
    return parser.parse_args()


def write_mainline(out: Path, readiness: dict) -> None:
    lines = [
        "# v1.0.8.2 Architecture Finalization and RedQueen Governance Bootstrap",
        "",
        "This version checks that the controlled opt-in architecture bridge landed, then bootstraps RedQueen as a read-only metrics-driven governance layer.",
        "",
        "It does not train models, update weights, change the default profile, enable real promotion, release, or claim production support completed.",
        "",
        f"- architecture finalization passed: `{readiness.get('architecture_finalization_passed')}`",
        f"- support scope codepath aligned: `{readiness.get('support_scope_codepath_aligned')}`",
        f"- metrics bus read only: `{readiness.get('metrics_bus_read_only')}`",
        f"- active review allocator completed: `{readiness.get('active_review_allocator_completed')}`",
        f"- difficulty scheduler completed: `{readiness.get('difficulty_scheduler_completed')}`",
        f"- self governance policy generated: `{readiness.get('governance_policy_generated')}`",
        f"- RedQueen dry-run passed: `{readiness.get('redqueen_dry_run_passed')}`",
        f"- next validation plan generated: `{readiness.get('next_validation_plan_generated')}`",
        f"- default profile unchanged: `{readiness.get('default_profile_unchanged')}`",
        f"- real promotion enabled: `{readiness.get('real_promotion_enabled')}`",
        f"- controlled opt-in support approved: `{readiness.get('controlled_opt_in_support_approved')}`",
        f"- production support completed: `false`",
        f"- recommended claim level: `{readiness.get('recommended_claim_level')}`",
        f"- blocking issues: `{readiness.get('blocking_issues')}`",
        f"- required next run: `{readiness.get('required_next_run')}`",
        "",
        "## Still Not Proven",
        "",
    ]
    lines.extend(f"- {item}" for item in STILL_NOT_PROVEN)
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "mainline_conclusion.json").write_text(json.dumps({"readiness": readiness, "still_not_proven": list(STILL_NOT_PROVEN)}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _checkpoint(out: Path, payload: dict) -> None:
    with (out / "redqueen_runner_checkpoints.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)


def _bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    raise SystemExit(main())
