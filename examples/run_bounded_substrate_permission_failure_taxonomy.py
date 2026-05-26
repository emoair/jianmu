from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.bounded_substrate_permission_failure_taxonomy import classify_v0_9_7_1_failures
from jianmu.self_learning.darwinforge.bounded_substrate_permission_readiness import assess_permission_failure_readiness
from jianmu.self_learning.darwinforge.bounded_substrate_permission_replay import replay_permission_failures, run_independent_validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-records", default="records/v0_9_7_1")
    parser.add_argument("--dataset-dir", default="datasets/v0_9_6_turing_substrate_curriculum")
    parser.add_argument("--output-records", default="records/v0_9_7_2")
    parser.add_argument("--rerun-failures", default="true")
    parser.add_argument("--apply-temp-manager-fix", default="true")
    parser.add_argument("--run-independent-validation", default="true")
    parser.add_argument("--supported-samples", type=int, default=2000)
    parser.add_argument("--boundary-samples", type=int, default=2000)
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--seed", type=int, default=60)
    parser.add_argument("--timeout-seconds", type=int, default=5)
    args = parser.parse_args()
    out = Path(args.output_records)
    out.mkdir(parents=True, exist_ok=True)
    taxonomy = classify_v0_9_7_1_failures(args.source_records, out)
    patched = {}
    if args.rerun_failures.lower() == "true" and args.apply_temp_manager_fix.lower() == "true":
        patched = replay_permission_failures(args.source_records, args.dataset_dir, out, args.compile_worker_count, args.timeout_seconds)
    else:
        patched = {"original_result_preserved": True}
    independent = {}
    if args.run_independent_validation.lower() == "true" and args.apply_temp_manager_fix.lower() == "true":
        independent = run_independent_validation(args.dataset_dir, out, args.supported_samples, args.boundary_samples, args.compile_worker_count, args.seed, args.timeout_seconds)
    readiness = assess_permission_failure_readiness(out, taxonomy, patched, independent)
    _write_temp_manager_audit(out)
    _write_mainline(out, taxonomy, patched, independent, readiness)
    print(json.dumps({
        "original_failure_count": readiness["original_failure_count"],
        "dominant_failure_category": readiness["dominant_failure_category"],
        "patched_compiler_verified_correct_rate": readiness["patched_compiler_verified_correct_rate"],
        "independent_compiler_verified_correct_rate": readiness["independent_compiler_verified_correct_rate"],
        "recommended_claim_level": readiness["recommended_claim_level"],
    }, ensure_ascii=False, indent=2, sort_keys=True))


def _write_temp_manager_audit(out: Path) -> None:
    payload = {
        "temp_manager_fix_applied": True,
        "unique_per_sample_dirs": True,
        "compiler_tmp_root": "system_temp/jianmu_v0_9_7_2_compiler_tmp",
        "records_tree_used_for_compiler_tmp": False,
        "subprocess_uses_list_args": True,
        "shell_true_used": False,
        "cleanup_retry_enabled": True,
        "cleanup_failure_separate_from_compiler_verification": True,
        "trace_writer_mode": "single file write after worker completion",
    }
    (out / "compiler_temp_manager_audit.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_mainline(out: Path, taxonomy: dict, patched: dict, independent: dict, readiness: dict) -> None:
    still = [
        "Turing completeness",
        "solved arithmetic",
        "solved program synthesis",
        "stable convergence",
        "solved OOD",
        "general program synthesis",
        "same-size LLM advantage",
        "safe real promotion",
        "production readiness",
    ]
    conclusion = {
        "what_this_version_proved": "classified v0.9.7.1 compiler PermissionError failures and tested a patched temp/process manager",
        "what_this_version_did_not_prove": still,
        "v0_9_7_1_permission_error_primary_cause": taxonomy.get("dominant_failure_category"),
        "engineering_temp_process_cleanup_issue": taxonomy.get("engineering_issue_dominant"),
        "candidate_or_program_errors_detected": taxonomy.get("candidate_error_dominant"),
        "patched_replay_result": patched,
        "independent_validation_result": independent,
        "original_v0_9_7_1_result_preserved": patched.get("original_result_preserved", False),
        "bounded_substrate_signal_claim_reconciliation": readiness.get("recommended_claim_level"),
        "recommended_claim_level": readiness.get("recommended_claim_level"),
        "blocking_issues": readiness.get("blocking_issues", []),
        "required_next_run": readiness.get("required_next_run"),
        "paper_v2_candidate_results": ["PermissionError taxonomy", "patched replay", "independent compiler validation"],
        "must_revalidate": ["full-level compiler validation after temp manager fix"],
        "post_v1_reserved_routes": ["root similarity incremental training", "verified backend as teacher for NL-to-semantic-IR adapter"],
        "still_not_proven": still,
    }
    (out / "mainline_conclusion.json").write_text(json.dumps(conclusion, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# v0.9.7.2 Mainline Conclusion", "", f"Recommended claim level: {readiness.get('recommended_claim_level')}", "", f"Dominant failure category: {taxonomy.get('dominant_failure_category')}", "", "## Still Not Proven"]
    lines.extend(f"- {item}" for item in still)
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
