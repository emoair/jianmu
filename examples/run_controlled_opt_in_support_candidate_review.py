from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.controlled_opt_in_failure_taxonomy import build_failure_taxonomy
from jianmu.self_learning.darwinforge.controlled_opt_in_negative_validation import run_negative_boundary_validation
from jianmu.self_learning.darwinforge.controlled_opt_in_positive_validation import run_positive_support_candidate_validation
from jianmu.self_learning.darwinforge.controlled_opt_in_rollback_review import build_default_rollback_regression_recheck
from jianmu.self_learning.darwinforge.controlled_opt_in_support_readiness import build_controlled_opt_in_support_readiness
from jianmu.self_learning.darwinforge.controlled_opt_in_support_reviewer import build_reviewer_support_pack
from jianmu.self_learning.darwinforge.controlled_opt_in_support_schema import ControlledOptInSupportConfig, STILL_NOT_PROVEN
from jianmu.self_learning.darwinforge.controlled_opt_in_trace_review import build_controlled_support_trace_pack
from jianmu.self_learning.darwinforge.controlled_support_scope_matrix import build_support_scope_matrix
from jianmu.self_learning.darwinforge.unsupported_boundary_matrix import build_unsupported_boundary_matrix


def main() -> int:
    args = parse_args()
    out = Path(args.output_records)
    out.mkdir(parents=True, exist_ok=True)
    _checkpoint(out, {"phase": "controlled_support_review_started"})
    config = ControlledOptInSupportConfig(
        profile_name=args.profile_name,
        workers=args.workers,
        compiler_workers=args.compiler_workers,
        negative_validation_events=args.negative_validation_events,
        positive_validation_events=args.positive_validation_events,
        minimum_real_compiler_invocations=args.minimum_real_compiler_invocations,
    )
    scope = build_support_scope_matrix(out)
    unsupported = build_unsupported_boundary_matrix(out)
    taxonomy = build_failure_taxonomy(out)
    negative = run_negative_boundary_validation(out, config, seed=_first_seed(args.seed))
    _checkpoint(out, {"phase": "negative_validation_completed", "events": negative["negative_validation_events"]})
    positive = run_positive_support_candidate_validation(out, config, seed=_first_seed(args.seed), progress=args.progress)
    _checkpoint(out, {"phase": "positive_validation_completed", "events": positive.get("positive_validation_events", 0), "real_compiler_invocations": positive.get("real_compiler_invocations", 0)})
    rollback = build_default_rollback_regression_recheck(out, positive, negative)
    trace_pack = build_controlled_support_trace_pack(out, positive.get("rows", []), negative.get("rows", []), positive.get("backend_report", {}))
    preview = {**negative, **positive, **rollback, **trace_pack, "recommended_claim_level": "pending"}
    reviewer = build_reviewer_support_pack(out, preview)
    readiness = build_controlled_opt_in_support_readiness(
        out,
        scope,
        unsupported,
        taxonomy,
        {k: v for k, v in negative.items() if k != "rows"},
        {k: v for k, v in positive.items() if k not in {"rows", "backend_report"}},
        rollback,
        trace_pack,
        reviewer,
        workers_requested=args.workers,
        workers_used=min(args.workers, args.compiler_workers, 16),
    )
    write_mainline(out, readiness)
    _checkpoint(out, {"phase": "readiness_completed", "recommended_claim_level": readiness["recommended_claim_level"]})
    print(json.dumps({"output_records": str(out), "recommended_claim_level": readiness["recommended_claim_level"], "controlled_opt_in_support_candidate_ready": readiness["controlled_opt_in_support_candidate_ready"]}, ensure_ascii=False, sort_keys=True), flush=True)
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
    ]:
        parser.add_argument(f"--{name}", default="")
    parser.add_argument("--output-records", default="records/v1_0_8_controlled_support")
    parser.add_argument("--profile-name", default="staged_opt_in_function_array_recursion_v1_0_7")
    parser.add_argument("--negative-validation-events", type=int, default=50_000)
    parser.add_argument("--positive-validation-events", type=int, default=50_000)
    parser.add_argument("--minimum-real-compiler-invocations", type=int, default=40_000)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--compiler-workers", type=int, default=16)
    parser.add_argument("--seed", default="213,214,215")
    parser.add_argument("--progress", type=_bool, default=False)
    for flag in [
        "controlled-support-review",
        "no-model-training",
        "no-weight-update",
        "explicit-opt-in-required",
        "forbid-default-profile-change",
        "forbid-default-bridge-leak",
        "forbid-real-promotion",
        "forbid-user-facing-enable",
        "forbid-release",
        "generate-support-scope-matrix",
        "generate-unsupported-boundary-matrix",
        "generate-failure-taxonomy",
        "run-negative-boundary-validation",
        "run-positive-support-validation",
        "accounting-lock",
        "require-v1-0-6-adapter-reuse",
        "require-atomic-policy-bridge",
        "require-extended-ir-path",
        "require-extended-emitter",
        "forbid-template-bypass",
        "forbid-marker-ir-direct-compile",
        "forbid-summary-only-validation",
        "run-default-rollback-regression-recheck",
        "build-reviewer-support-pack",
        "run-claim-boundary-review",
        "run-architecture-charter-guard",
    ]:
        parser.add_argument(f"--{flag}", type=_bool, default=True)
    parser.add_argument("--trace-writer-mode", default="sharded")
    parser.add_argument("--temp-dir-mode", default="per_sample")
    return parser.parse_args()


def write_mainline(out: Path, readiness: Dict[str, Any]) -> None:
    md = [
        "# v1.0.8 Controlled Opt-in Support Candidate Review",
        "",
        "This version reviews the staged opt-in bridge as a controlled support candidate. It does not train models, update weights, change the default profile, enable real promotion, enable user-facing production, release, or claim production support completed.",
        "",
        f"- staged opt-in profile: `{readiness.get('profile_name', 'staged_opt_in_function_array_recursion_v1_0_7')}`",
        f"- default profile unchanged: `{readiness.get('default_profile_unchanged')}`",
        f"- explicit opt-in required: `{readiness.get('explicit_opt_in_required')}`",
        f"- real promotion enabled: `{readiness.get('real_promotion_enabled')}`",
        f"- negative validation events: `{readiness.get('negative_validation_events')}`",
        f"- positive validation events: `{readiness.get('positive_validation_events')}`",
        f"- real compiler invocations: `{readiness.get('real_compiler_invocations')}`",
        f"- trace pack replayable: `{readiness.get('trace_pack_replayable')}`",
        f"- reviewer support pack: `records/v1_0_8_controlled_support/reviewer_support_pack/`",
        f"- controlled_opt_in_support_candidate_ready: `{readiness.get('controlled_opt_in_support_candidate_ready')}`",
        f"- production support completed: `false`",
        f"- recommended_claim_level: `{readiness.get('recommended_claim_level')}`",
        f"- blocking_issues: `{readiness.get('blocking_issues')}`",
        f"- required_next_run: `{readiness.get('required_next_run')}`",
        "",
        "## Still Not Proven",
        "",
    ]
    md.extend(f"- {item}" for item in STILL_NOT_PROVEN)
    (out / "mainline_conclusion.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (out / "mainline_conclusion.json").write_text(json.dumps({"readiness": readiness, "still_not_proven": list(STILL_NOT_PROVEN)}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _checkpoint(out: Path, payload: Dict[str, Any]) -> None:
    with (out / "controlled_support_runner_checkpoints.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)


def _bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


def _first_seed(value: str) -> int:
    return int(str(value).split(",", 1)[0])


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        out = Path("records/v1_0_8_controlled_support")
        out.mkdir(parents=True, exist_ok=True)
        (out / "controlled_support_runner_failure.json").write_text(json.dumps({"failure_type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        raise
