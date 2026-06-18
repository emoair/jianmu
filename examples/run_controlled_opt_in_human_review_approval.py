from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.approval_gate_verdict import build_approval_gate_verdict
from jianmu.self_learning.darwinforge.controlled_opt_in_approval_readiness import build_controlled_opt_in_approval_readiness
from jianmu.self_learning.darwinforge.controlled_opt_in_approval_schema import ApprovalGateConfig, STILL_NOT_PROVEN
from jianmu.self_learning.darwinforge.evidence_sampling_review import run_evidence_sampling_review
from jianmu.self_learning.darwinforge.failure_taxonomy_completeness_audit import audit_failure_taxonomy_completeness
from jianmu.self_learning.darwinforge.historical_records_write_audit import audit_historical_records_write_policy
from jianmu.self_learning.darwinforge.human_review_checklist_audit import audit_reviewer_pack
from jianmu.self_learning.darwinforge.support_scope_overclaim_audit import audit_support_scope_overclaim
from jianmu.self_learning.darwinforge.unsupported_boundary_gap_audit import audit_unsupported_boundary_gap
from jianmu.self_learning.darwinforge.windows_onedrive_records_isolation import audit_windows_onedrive_records_isolation


def main() -> int:
    args = parse_args()
    out = Path(args.output_records)
    out.mkdir(parents=True, exist_ok=True)
    _checkpoint(out, {"phase": "approval_review_started"})
    config = ApprovalGateConfig(
        profile_name=args.profile_name,
        workers=args.workers,
        positive_samples=args.positive_samples,
        negative_samples=args.negative_samples,
        rollback_samples=args.rollback_samples,
        policy_path_samples=args.policy_path_samples,
        stdout_samples=args.stdout_samples,
        unsupported_rejection_samples=args.unsupported_rejection_samples,
        default_blocking_samples=args.default_blocking_samples,
    )
    source = Path(args.source_records_v1_0_8)
    reviewer = audit_reviewer_pack(source, out)
    scope = audit_support_scope_overclaim(source, out)
    unsupported = audit_unsupported_boundary_gap(source, out)
    taxonomy = audit_failure_taxonomy_completeness(source, out)
    sampling = run_evidence_sampling_review(source, out, config, seed=_first_seed(args.seed))
    isolation = audit_windows_onedrive_records_isolation(out, ROOT)
    audit_historical_records_write_policy(out)
    write_signoff_template(out)
    readiness_path = source / "controlled_opt_in_support_readiness.json"
    candidate_ready = json.loads(readiness_path.read_text(encoding="utf-8")).get("controlled_opt_in_support_candidate_ready") is True
    verdict = build_approval_gate_verdict(out, {"reviewer": reviewer, "scope": scope, "unsupported": unsupported, "taxonomy": taxonomy, "sampling": sampling, "isolation": isolation}, candidate_ready=candidate_ready)
    readiness = build_controlled_opt_in_approval_readiness(out, verdict, isolation)
    write_mainline(out, readiness)
    _checkpoint(out, {"phase": "approval_readiness_completed", "recommended_claim_level": readiness["recommended_claim_level"], "approval_status": readiness["approval_status"]})
    print(json.dumps({"output_records": str(out), "approval_status": readiness["approval_status"], "recommended_claim_level": readiness["recommended_claim_level"]}, ensure_ascii=False, sort_keys=True), flush=True)
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
        "source-records-v1-0-8",
    ]:
        parser.add_argument(f"--{name}", default="")
    parser.add_argument("--output-records", default="records/v1_0_8_1_approval")
    parser.add_argument("--profile-name", default="staged_opt_in_function_array_recursion_v1_0_7")
    parser.add_argument("--positive-samples", type=int, default=1000)
    parser.add_argument("--negative-samples", type=int, default=1000)
    parser.add_argument("--rollback-samples", type=int, default=300)
    parser.add_argument("--policy-path-samples", type=int, default=300)
    parser.add_argument("--stdout-samples", type=int, default=1000)
    parser.add_argument("--unsupported-rejection-samples", type=int, default=500)
    parser.add_argument("--default-blocking-samples", type=int, default=500)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--seed", default="216,217,218")
    parser.add_argument("--progress", type=_bool, default=False)
    for flag in [
        "human-review-approval-gate",
        "no-model-training",
        "no-weight-update",
        "explicit-opt-in-required",
        "forbid-default-profile-change",
        "forbid-default-bridge-leak",
        "forbid-real-promotion",
        "forbid-user-facing-enable",
        "forbid-release",
        "run-reviewer-pack-audit",
        "run-support-scope-overclaim-audit",
        "run-unsupported-boundary-gap-audit",
        "run-failure-taxonomy-completeness-audit",
        "run-evidence-sampling-review",
        "run-windows-onedrive-records-isolation",
        "require-v1-0-6-adapter-reuse",
        "require-atomic-policy-bridge",
        "require-extended-ir-path",
        "require-extended-emitter",
        "forbid-template-bypass",
        "forbid-marker-ir-direct-compile",
        "forbid-summary-only-validation",
        "build-review-signoff-template",
        "run-claim-boundary-review",
        "run-architecture-charter-guard",
    ]:
        parser.add_argument(f"--{flag}", type=_bool, default=True)
    return parser.parse_args()


def write_signoff_template(out: Path) -> None:
    text = """# Controlled Opt-in Support Review Signoff

Reviewer:

Date:

Decision:

* [ ] approved
* [ ] approved_with_notes
* [ ] not_approved

Reviewed:

* [ ] support scope matrix
* [ ] unsupported boundary matrix
* [ ] failure taxonomy
* [ ] negative validation
* [ ] positive validation
* [ ] trace pack
* [ ] rollback evidence
* [ ] Windows / OneDrive records isolation
* [ ] claim boundary

Notes:

Signature / Initials:
"""
    (out / "REVIEW_SIGNOFF.md").write_text(text, encoding="utf-8")


def write_mainline(out: Path, readiness: dict) -> None:
    lines = [
        "# v1.0.8.1 Controlled Opt-in Human Review and Approval Gate",
        "",
        "This version reviews the v1.0.8 controlled opt-in support candidate evidence package and runs an approval gate.",
        "",
        "It does not train a model, update weights, change the default profile, enable real promotion, enable user-facing production, release, or claim production support completed.",
        "",
        f"- staged opt-in profile: `{readiness.get('profile_name', 'staged_opt_in_function_array_recursion_v1_0_7')}`",
        f"- default profile unchanged: `{readiness.get('default_profile_unchanged')}`",
        f"- explicit opt-in required: `{readiness.get('explicit_opt_in_required')}`",
        f"- real promotion enabled: `{readiness.get('real_promotion_enabled')}`",
        f"- reviewer pack audit passed: `{readiness.get('reviewer_pack_audit_passed')}`",
        f"- support scope audit passed: `{readiness.get('support_scope_audit_passed')}`",
        f"- unsupported boundary audit passed: `{readiness.get('unsupported_boundary_audit_passed')}`",
        f"- failure taxonomy audit passed: `{readiness.get('failure_taxonomy_audit_passed')}`",
        f"- evidence sampling passed: `{readiness.get('evidence_sampling_passed')}`",
        f"- Windows / OneDrive isolation passed: `{readiness.get('windows_onedrive_isolation_passed')}`",
        f"- approval status: `{readiness.get('approval_status')}`",
        f"- approval recommended: `{readiness.get('controlled_opt_in_support_approval_recommended')}`",
        f"- controlled opt-in support approved: `{readiness.get('controlled_opt_in_support_approved')}`",
        f"- human signoff required: `{readiness.get('human_signoff_required')}`",
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
    with (out / "approval_runner_checkpoints.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)


def _bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


def _first_seed(value: str) -> int:
    return int(str(value).split(",", 1)[0])


if __name__ == "__main__":
    raise SystemExit(main())
