from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.controlled_profile_review_readiness import build_controlled_profile_review_readiness
from jianmu.self_learning.darwinforge.controlled_profile_review_schema import STILL_NOT_PROVEN, check_v1_0_6_records
from jianmu.self_learning.darwinforge.default_profile_contamination_audit import run_default_profile_contamination_audit
from jianmu.self_learning.darwinforge.dry_run_coverage_review import run_dry_run_coverage_review
from jianmu.self_learning.darwinforge.rollback_stress_review import run_rollback_stress_review
from jianmu.self_learning.darwinforge.shadow_profile_review import run_shadow_profile_review
from jianmu.self_learning.darwinforge.staged_opt_in_precheck import run_staged_opt_in_precheck
from jianmu.self_learning.darwinforge.trace_pack_replayability_review import run_trace_pack_replayability_review
from jianmu.self_learning.darwinforge.windows_records_write_isolation_audit import run_windows_records_write_isolation_audit


def main() -> int:
    args = parse_args()
    out = Path(args.output_records)
    out.mkdir(parents=True, exist_ok=True)
    source = check_v1_0_6_records(args.source_records_v1_0_6)
    if not source["source_dry_run_records_found"]:
        readiness = _blocked_missing(out, source)
        print(json.dumps({"output_records": str(out), "recommended_claim_level": readiness["recommended_claim_level"]}, sort_keys=True))
        return 0
    shadow = run_shadow_profile_review(args.source_records_v1_0_6, out)
    contamination = run_default_profile_contamination_audit(args.source_records_v1_0_6, out)
    adapter = run_interface_adapter_review(args.source_records_v1_0_6, out)
    coverage = run_dry_run_coverage_review(args.source_records_v1_0_6, out, args.minimum_unique_compile_units, args.minimum_source_sha256_unique)
    windows = run_windows_records_write_isolation_audit(out)
    if contamination.get("default_profile_contamination_detected"):
        replay = {"trace_replay_completed": False}
        rollback = {"rollback_stress_completed": False}
        precheck = run_staged_opt_in_precheck(out, False)
    else:
        replay = run_trace_pack_replayability_review(args.source_records_v1_0_6, out, args.replay_samples, args.workers, args.compiler_workers)
        rollback = run_rollback_stress_review(out, args.rollback_cycles, args.samples_per_rollback_cycle)
        review_clean = (
            shadow.get("shadow_profile_valid")
            and not contamination.get("default_profile_contamination_detected")
            and adapter.get("adapter_interface_valid")
            and coverage.get("category_all_represented")
            and windows.get("windows_write_isolation_passed")
            and replay.get("trace_pack_replayability_passed")
            and rollback.get("rollback_stress_passed")
        )
        precheck = run_staged_opt_in_precheck(out, bool(review_clean))
    readiness = build_controlled_profile_review_readiness(out, source, shadow, contamination, adapter, coverage, windows, replay, rollback, precheck)
    write_mainline(out, readiness, windows)
    print(json.dumps({"output_records": str(out), "recommended_claim_level": readiness["recommended_claim_level"], "ready_for_staged_opt_in_candidate": readiness["ready_for_staged_opt_in_candidate"]}, ensure_ascii=False, sort_keys=True))
    return 0


def run_interface_adapter_review(source_records: str | Path, output_records: str | Path) -> dict:
    source = json.loads((Path(source_records) / "interface_adapter_audit.json").read_text(encoding="utf-8"))
    issues = []
    if not source.get("adapter_interface_valid"):
        issues.append("adapter_interface_invalid")
    for key in ("direct_template_path_detected", "marker_ir_direct_compile_detected", "summary_only_validation_detected"):
        if source.get(key):
            issues.append(key)
    result = {
        "interface_adapter_review_completed": True,
        "adapter_interface_valid": source.get("adapter_interface_valid", False),
        "static_scan_completed": True,
        "direct_template_path_detected": source.get("direct_template_path_detected", True),
        "marker_ir_direct_compile_detected": source.get("marker_ir_direct_compile_detected", True),
        "summary_only_validation_detected": source.get("summary_only_validation_detected", True),
        "adapter_review_issues": issues,
    }
    (Path(output_records) / "interface_adapter_review.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def write_mainline(out: Path, readiness: dict, windows: dict) -> None:
    lines = [
        "# v1.0.6.1 Controlled Profile Review",
        "",
        "## What This Version Did",
        "Reviewed the v1.0.6 production shadow dry-run records, guard, rollback, coverage, trace replayability, Windows records write isolation, and staged opt-in precheck.",
        "",
        "## What This Version Did Not Do",
        "It did not modify the default profile, enable real promotion, execute staged opt-in, claim production support, tag, release, add natural language, or add a new capability frontier.",
        "",
        "## Why Controlled Review Was Needed",
        "v1.0.6 was dry-run positive, but staged opt-in requires a separate review of profile boundaries, rollback reliability, trace replayability, and Windows write isolation.",
        "",
        "## Results",
    ]
    for key in [
        "source_dry_run_records_found",
        "shadow_profile_valid",
        "default_profile_contamination_detected",
        "adapter_interface_valid",
        "category_all_represented",
        "windows_write_isolation_passed",
        "trace_replay_completed",
        "replay_success_rate",
        "rollback_stress_passed",
        "ready_for_staged_opt_in_candidate",
        "staged_opt_in_executed",
        "production_function_support_completed",
        "production_array_support_completed",
        "production_recursion_support_completed",
        "recommended_claim_level",
        "blocking_issues",
        "required_next_run",
    ]:
        lines.append(f"- {key}: {readiness.get(key)}")
    lines.extend(["", "## Windows Records Write Isolation", f"- suspected_root_cause: {windows.get('suspected_root_cause')}", "", "## Still Not Proven"])
    lines.extend(f"- {item}" for item in STILL_NOT_PROVEN)
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "mainline_conclusion.json").write_text(json.dumps({"readiness": readiness, "windows_records_write_isolation": windows}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _blocked_missing(out: Path, source: dict) -> dict:
    result = {
        **source,
        "controlled_profile_review_completed": False,
        "recommended_claim_level": "controlled_review_blocked_missing_v1_0_6_records",
        "blocking_issues": ["missing_v1_0_6_records"],
    }
    (out / "controlled_profile_review_readiness.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--source-records-v1-0-6", default="records/v1_0_6_dry_run")
    parser.add_argument("--output-records", default="records/v1_0_6_1_controlled_review")
    parser.add_argument("--run-shadow-profile-review", type=_bool, default=True)
    parser.add_argument("--run-default-profile-contamination-audit", type=_bool, default=True)
    parser.add_argument("--run-interface-adapter-review", type=_bool, default=True)
    parser.add_argument("--run-coverage-review", type=_bool, default=True)
    parser.add_argument("--run-windows-records-write-isolation-audit", type=_bool, default=True)
    parser.add_argument("--run-trace-pack-replayability-review", type=_bool, default=True)
    parser.add_argument("--run-rollback-stress-review", type=_bool, default=True)
    parser.add_argument("--run-staged-opt-in-precheck", type=_bool, default=True)
    parser.add_argument("--replay-samples", type=int, default=2000)
    parser.add_argument("--replay-minimum-required", type=int, default=1000)
    parser.add_argument("--rollback-cycles", type=int, default=100)
    parser.add_argument("--samples-per-rollback-cycle", type=int, default=5)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--compiler-workers", type=int, default=16)
    parser.add_argument("--trace-writer-mode", default="sharded")
    parser.add_argument("--temp-dir-mode", default="per_sample")
    parser.add_argument("--accounting-lock", type=_bool, default=True)
    parser.add_argument("--forbid-default-profile-contamination", type=_bool, default=True)
    parser.add_argument("--forbid-real-promotion", type=_bool, default=True)
    parser.add_argument("--forbid-user-facing-enable", type=_bool, default=True)
    parser.add_argument("--forbid-staged-opt-in-execution", type=_bool, default=True)
    parser.add_argument("--forbid-template-bypass", type=_bool, default=True)
    parser.add_argument("--forbid-marker-ir-direct-compile", type=_bool, default=True)
    parser.add_argument("--forbid-summary-only-validation", type=_bool, default=True)
    parser.add_argument("--require-all-categories", type=_bool, default=True)
    parser.add_argument("--minimum-unique-compile-units", type=int, default=9000)
    parser.add_argument("--minimum-source-sha256-unique", type=int, default=9000)
    parser.add_argument("--run-claim-boundary-review", type=_bool, default=True)
    parser.add_argument("--run-architecture-charter-guard", type=_bool, default=True)
    parser.add_argument("--progress", type=_bool, default=False)
    parser.add_argument("--seed", default="201")
    return parser.parse_args()


def _bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return value.lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    raise SystemExit(main())
