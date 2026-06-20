from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.redqueen_governance_drift_audit import audit_governance_drift
from jianmu.self_learning.darwinforge.redqueen_iteration_readiness import build_redqueen_iteration_readiness
from jianmu.self_learning.darwinforge.redqueen_iteration_schema import RedQueenIterationConfig, STILL_NOT_PROVEN_ITERATION
from jianmu.self_learning.darwinforge.redqueen_metric_delta import create_post_iteration_metrics_snapshot, create_pre_iteration_metrics_snapshot, review_metric_delta
from jianmu.self_learning.darwinforge.redqueen_next_plan_updater import update_redqueen_next_plan
from jianmu.self_learning.darwinforge.redqueen_plan_executor import execute_redqueen_plan
from jianmu.self_learning.darwinforge.redqueen_plan_loader import load_redqueen_iteration_plan
from jianmu.self_learning.darwinforge.redqueen_underreaction_audit import audit_over_under_reaction


def main() -> int:
    args = parse_args()
    out = Path(args.output_records)
    out.mkdir(parents=True, exist_ok=True)
    cfg = RedQueenIterationConfig(
        profile_name=args.profile_name,
        iteration_index=args.iteration_index,
        iteration_events=args.iteration_events,
        minimum_real_compiler_invocations=args.minimum_real_compiler_invocations,
        workers=args.workers,
        compiler_workers=args.compiler_workers,
        require_plan_follow_rate=args.require_plan_follow_rate,
    )
    _checkpoint(out, {"phase": "redqueen_iteration_started"})
    loader = load_redqueen_iteration_plan(args.source_records_v1_0_8_2, out)
    if loader.get("plan_loader_passed"):
        pre = create_pre_iteration_metrics_snapshot(out, loader)
        execution = execute_redqueen_plan(out, loader, cfg)
        post = create_post_iteration_metrics_snapshot(out, pre, execution)
        delta = review_metric_delta(out, pre, post)
        drift = audit_governance_drift(out, execution)
        reaction = audit_over_under_reaction(out, pre, post, execution)
        next_plan = update_redqueen_next_plan(out, loader, delta)
    else:
        pre = {"pre_metrics_snapshot_created": False}
        execution = {"plan_execution_completed": False}
        post = {"post_metrics_snapshot_created": False}
        delta = {"metric_delta_review_completed": False}
        drift = {"governance_drift_audit_passed": False}
        reaction = {"over_under_reaction_audit_passed": False}
        next_plan = {"next_plan_v2_generated": False}
    readiness = build_redqueen_iteration_readiness(out, loader, pre, execution, post, delta, drift, reaction, next_plan)
    write_mainline(out, readiness)
    _checkpoint(out, {"phase": "redqueen_iteration_completed", "recommended_claim_level": readiness["recommended_claim_level"]})
    print(json.dumps({"output_records": str(out), "recommended_claim_level": readiness["recommended_claim_level"], "redqueen_governance_iteration_1_positive": readiness["redqueen_governance_iteration_1_positive"]}, ensure_ascii=False, sort_keys=True), flush=True)
    return 0 if readiness["recommended_claim_level"] != "failed" else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    for name in ["source-records-v1-0-5-1", "source-records-v1-0-5-2", "source-records-v1-0-6", "source-records-v1-0-6-1", "source-records-v1-0-7", "source-records-v1-0-7-1", "source-records-v1-0-7-2", "source-records-v1-0-8", "source-records-v1-0-8-1", "source-records-v1-0-8-2"]:
        parser.add_argument(f"--{name}", default="")
    parser.add_argument("--output-records", default="records/v1_0_8_3_redqueen_iteration_1")
    parser.add_argument("--profile-name", default="staged_opt_in_function_array_recursion_v1_0_7")
    parser.add_argument("--iteration-index", type=int, default=1)
    parser.add_argument("--iteration-events", type=int, default=60_000)
    parser.add_argument("--minimum-real-compiler-invocations", type=int, default=40_000)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--compiler-workers", type=int, default=16)
    parser.add_argument("--require-plan-follow-rate", type=float, default=0.95)
    parser.add_argument("--seed", default="222,223,224")
    parser.add_argument("--trace-writer-mode", default="sharded")
    parser.add_argument("--temp-dir-mode", default="per_sample")
    for flag in [
        "redqueen-governance-iteration",
        "load-previous-redqueen-plan",
        "execute-redqueen-plan",
        "compare-pre-post-metrics",
        "generate-next-plan-v2",
        "no-model-training",
        "no-weight-update",
        "explicit-opt-in-required",
        "forbid-default-profile-change",
        "forbid-default-bridge-leak",
        "forbid-real-promotion",
        "forbid-user-facing-enable",
        "forbid-release",
        "accounting-lock",
        "require-weak-category-review-boost",
        "require-stable-category-annealing",
        "require-coverage-gap-shape-diversity",
        "require-boundary-minimum-review",
        "require-v1-0-6-adapter-reuse",
        "require-atomic-policy-bridge",
        "require-extended-ir-path",
        "require-extended-emitter",
        "forbid-template-bypass",
        "forbid-marker-ir-direct-compile",
        "forbid-summary-only-validation",
        "run-governance-drift-audit",
        "run-overreaction-audit",
        "run-underreaction-audit",
        "run-claim-boundary-review",
        "run-architecture-charter-guard",
        "progress",
    ]:
        parser.add_argument(f"--{flag}", type=_bool, default=True)
    return parser.parse_args()


def write_mainline(out: Path, readiness: dict) -> None:
    lines = [
        "# v1.0.8.3 RedQueen Governance Iteration 1",
        "",
        "This version executes the first RedQueen governance iteration from the v1.0.8.2 next validation plan.",
        "",
        "It does not train models, update weights, modify the default profile, enable real promotion, enable user-facing production, release, or claim production support completed.",
        "",
        f"- source plan loaded: `{readiness.get('source_plan_loaded')}`",
        f"- pre metrics snapshot created: `{readiness.get('pre_metrics_snapshot_created')}`",
        f"- plan execution completed: `{readiness.get('plan_execution_completed')}`",
        f"- post metrics snapshot created: `{readiness.get('post_metrics_snapshot_created')}`",
        f"- metric delta review completed: `{readiness.get('metric_delta_review_completed')}`",
        f"- weak category received more review: `{readiness.get('weak_category_received_more_review')}`",
        f"- stable category annealed: `{readiness.get('stable_category_annealed')}`",
        f"- coverage gap category received shape diversity: `{readiness.get('coverage_gap_category_received_shape_diversity')}`",
        f"- boundary minimum review preserved: `{readiness.get('default_boundary_minimum_review_preserved') and readiness.get('unsupported_boundary_minimum_review_preserved')}`",
        f"- governance drift audit passed: `{readiness.get('governance_drift_audit_passed')}`",
        f"- over/under reaction audit passed: `{readiness.get('over_under_reaction_audit_passed')}`",
        f"- next plan v2 generated: `{readiness.get('next_plan_v2_generated')}`",
        f"- default profile unchanged: `{readiness.get('default_profile_unchanged')}`",
        f"- real promotion enabled: `{readiness.get('real_promotion_enabled')}`",
        f"- production support completed: `false`",
        f"- RedQueen autonomous governance completed: `{readiness.get('redqueen_autonomous_governance_completed')}`",
        f"- recommended claim level: `{readiness.get('recommended_claim_level')}`",
        f"- blocking issues: `{readiness.get('blocking_issues')}`",
        f"- required next run: `{readiness.get('required_next_run')}`",
        "",
        "## Still Not Proven",
        "",
    ]
    lines.extend(f"- {item}" for item in STILL_NOT_PROVEN_ITERATION)
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "mainline_conclusion.json").write_text(json.dumps({"readiness": readiness, "still_not_proven": list(STILL_NOT_PROVEN_ITERATION)}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _checkpoint(out: Path, payload: dict) -> None:
    with (out / "redqueen_iteration_runner_checkpoints.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)


def _bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    raise SystemExit(main())
