from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.mirror_cosymbiosis_metrics import build_mirror_cosymbiosis_metrics
from jianmu.self_learning.darwinforge.mirror_freeze_state_machine import run_mirror_freeze_state_machine
from jianmu.self_learning.darwinforge.mirror_landing_readiness import build_mirror_landing_readiness, classify_mirror_landing
from jianmu.self_learning.darwinforge.mirror_landing_runtime_probe import run_mirror_runtime_probe
from jianmu.self_learning.darwinforge.mirror_landing_schema import MirrorRuntimeProbeConfig
from jianmu.self_learning.darwinforge.mirror_landing_source_audit import audit_mirror_landing_source
from jianmu.self_learning.darwinforge.mirror_negative_boundary_audit import run_mirror_negative_boundary_audit
from jianmu.self_learning.darwinforge.mirror_redqueen_integration import integrate_mirror_metrics_with_redqueen
from jianmu.self_learning.darwinforge.redqueen_plan_loader import load_redqueen_iteration_plan
from jianmu.self_learning.darwinforge.redqueen_truth_gate import run_redqueen_truth_gate
from jianmu.self_learning.darwinforge.redqueen_truth_gate_schema import STILL_NOT_PROVEN_MIRROR


def main() -> int:
    args = parse_args()
    out = Path(args.output_records)
    out.mkdir(parents=True, exist_ok=True)
    truth = run_redqueen_truth_gate(
        out,
        args.records_root,
        args.source_records_v1_0_8_2,
        args.source_records_v1_0_8_6_1,
    )
    if not truth["redqueen_truth_gate_passed"]:
        readiness = build_mirror_landing_readiness(out, {**truth, "landing_classification": "blocked"})
        write_report(out, readiness)
        print(json.dumps({"recommended_claim_level": readiness["recommended_claim_level"], "redqueen_truth_gate_passed": False}, ensure_ascii=False, sort_keys=True), flush=True)
        return 1

    source = audit_mirror_landing_source(out, ROOT)
    repair_applied = source.get("landing_status") != "preexisting_runtime_landed"
    state = run_mirror_freeze_state_machine(out, preexisting_reused=bool(source.get("mirror_state_machine_found")))
    metrics = build_mirror_cosymbiosis_metrics(out, args.events)
    integration = integrate_mirror_metrics_with_redqueen(out, metrics)
    plan = load_redqueen_iteration_plan(args.source_records_v1_0_8_2, out).get("plan", {})
    probe = run_mirror_runtime_probe(out, plan, MirrorRuntimeProbeConfig(events=args.events, minimum_real_compiler_invocations=args.minimum_real_compiler_invocations, phases=args.phases, workers=args.workers, compiler_workers=args.compiler_workers))
    negative = run_mirror_negative_boundary_audit(out)
    classification = classify_mirror_landing(out, source, bool(repair_applied), probe, negative, integration)
    payload = {
        **truth,
        **source,
        **state,
        **metrics,
        **integration,
        **probe,
        **negative,
        **classification,
        "lane_swap_found": bool(source.get("lane_swap_found") or state.get("lane_swap_supported")),
        "cosymbiosis_metrics_found": bool(source.get("cosymbiosis_metrics_found") or metrics.get("cosymbiosis_metrics_passed")),
        "landing_repair_applied": bool(repair_applied),
        "explicit_opt_in_required": True,
        "user_facing_enabled": False,
        "official_release_enabled": False,
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "redqueen_autonomous_governance_completed": False,
    }
    readiness = build_mirror_landing_readiness(out, payload)
    write_report(out, readiness)
    print(json.dumps({"recommended_claim_level": readiness["recommended_claim_level"], "landing_classification": readiness.get("landing_classification")}, ensure_ascii=False, sort_keys=True), flush=True)
    return 0 if readiness["recommended_claim_level"] != "failed" else 1


def write_report(out: Path, readiness: dict) -> None:
    lines = [
        "# v1.0.8.7 RedQueen Truth Gate and Mirror Alternating-Freeze Landing Audit",
        "",
        "## What This Version Did",
        "",
        "This version first checks the RedQueen foundation against v1.0.8.6.1 time-integrity repair, then audits and minimally lands a mirror alternating-freeze path when preexisting runtime landing is not confirmed.",
        "",
        "## What This Version Did Not Do",
        "",
        "- It did not restore the old v1.0.8.6 8h claim.",
        "- It did not modify the default profile.",
        "- It did not enable real promotion, user-facing production, release, or natural-language support.",
        "- It did not claim production function, array, or recursion support completed.",
        "",
        "## Results",
        "",
        f"- RedQueen truth gate passed: `{readiness.get('redqueen_truth_gate_passed')}`",
        f"- v1.0.8.6 old 8h claim downgraded: `{readiness.get('v1_0_8_6_old_8h_claim_downgraded')}`",
        f"- source audit completed: `{readiness.get('mirror_source_audit_completed')}`",
        f"- preexisting runtime landing found: `{readiness.get('mirror_preexisting_landing_found')}`",
        f"- docs only detected: `{readiness.get('mirror_docs_only_detected')}`",
        f"- minimal landing repair applied: `{readiness.get('landing_repair_applied')}`",
        f"- state machine passed: `{readiness.get('state_machine_passed')}`",
        f"- frozen mutation rejected: `{readiness.get('frozen_mutation_rejected')}`",
        f"- lane swap supported: `{readiness.get('lane_swap_supported')}`",
        f"- co-symbiosis metrics passed: `{readiness.get('cosymbiosis_metrics_passed')}`",
        f"- RedQueen integration passed: `{readiness.get('mirror_redqueen_integration_passed')}`",
        f"- runtime probe passed: `{readiness.get('mirror_runtime_probe_passed')}`",
        f"- negative boundary audit passed: `{readiness.get('mirror_negative_boundary_audit_passed')}`",
        f"- landing classification: `{readiness.get('landing_classification')}`",
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
    lines.extend(f"- {item}" for item in STILL_NOT_PROVEN_MIRROR)
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "mainline_conclusion.json").write_text(json.dumps({"readiness": readiness, "still_not_proven": list(STILL_NOT_PROVEN_MIRROR)}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    for name in [
        "source-records-v1-0-5-1", "source-records-v1-0-5-2", "source-records-v1-0-6", "source-records-v1-0-6-1",
        "source-records-v1-0-7", "source-records-v1-0-7-1", "source-records-v1-0-7-2", "source-records-v1-0-8",
        "source-records-v1-0-8-1", "source-records-v1-0-8-2", "source-records-v1-0-8-3", "source-records-v1-0-8-3-1",
        "source-records-v1-0-8-4", "source-records-v1-0-8-5", "source-records-v1-0-8-6", "source-records-v1-0-8-6-1",
    ]:
        parser.add_argument(f"--{name}", default="")
    parser.add_argument("--output-records", default="records/v1_0_8_7_mirror_landing")
    parser.add_argument("--profile-name", default="staged_opt_in_function_array_recursion_v1_0_7")
    parser.add_argument("--events", type=int, default=30_000)
    parser.add_argument("--minimum-real-compiler-invocations", type=int, default=15_000)
    parser.add_argument("--phases", type=int, default=4)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--compiler-workers", type=int, default=16)
    parser.add_argument("--trace-writer-mode", default="sharded")
    parser.add_argument("--temp-dir-mode", default="per_sample")
    parser.add_argument("--seed", default="240,241,242")
    for flag in [
        "redqueen-truth-gate", "reject-old-v1-0-8-6-8h-claim", "require-time-integrity-repair", "mirror-landing-source-audit",
        "audit-mirror-terms", "allow-minimal-landing-repair", "require-honest-landing-classification", "run-mirror-freeze-state-machine",
        "run-mirror-cosymbiosis-metrics", "run-mirror-redqueen-integration", "run-mirror-runtime-probe", "accounting-lock",
        "use-monotonic-timing", "record-heartbeat", "run-mirror-negative-boundary-audit", "no-model-training", "no-weight-update",
        "explicit-opt-in-required", "forbid-default-profile-change", "forbid-default-bridge-leak", "forbid-real-promotion",
        "forbid-user-facing-enable", "forbid-release", "require-v1-0-6-adapter-reuse", "require-atomic-policy-bridge",
        "require-extended-ir-path", "require-extended-emitter", "forbid-template-bypass", "forbid-marker-ir-direct-compile",
        "forbid-summary-only-validation", "run-claim-boundary-review", "run-architecture-charter-guard", "progress",
    ]:
        parser.add_argument(f"--{flag}", type=_bool, default=True)
    return parser.parse_args()


def _bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    raise SystemExit(main())
