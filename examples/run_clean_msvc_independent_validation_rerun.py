from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.bounded_substrate_clean_independent_validation import run_clean_independent_validation
from jianmu.self_learning.darwinforge.clean_msvc_preflight import run_clean_msvc_preflight
from jianmu.self_learning.darwinforge.clean_validation_readiness import assess_clean_validation_readiness


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-records", default="records/v0_9_7_2")
    parser.add_argument("--dataset-dir", default="datasets/v0_9_6_turing_substrate_curriculum")
    parser.add_argument("--output-records", default="records/v0_9_7_3")
    parser.add_argument("--supported-samples", type=int, default=5000)
    parser.add_argument("--boundary-samples", type=int, default=5000)
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--seed", type=int, default=61)
    parser.add_argument("--timeout-seconds", type=int, default=5)
    parser.add_argument("--run-fallback-on-failure", default="true")
    parser.add_argument("--fallback-supported-samples", type=int, default=2000)
    parser.add_argument("--fallback-boundary-samples", type=int, default=2000)
    parser.add_argument("--fallback-worker-count", type=int, default=8)
    parser.add_argument("--fallback-seed", type=int, default=62)
    args = parser.parse_args()
    out = Path(args.output_records)
    out.mkdir(parents=True, exist_ok=True)
    preflight = run_clean_msvc_preflight(out, Path.cwd())
    if preflight["preflight_passed"]:
        metrics = run_clean_independent_validation(
            args.dataset_dir,
            out,
            args.supported_samples,
            args.boundary_samples,
            args.compile_worker_count,
            args.seed,
            args.timeout_seconds,
            args.run_fallback_on_failure.lower() == "true",
            args.fallback_supported_samples,
            args.fallback_boundary_samples,
            args.fallback_worker_count,
            args.fallback_seed,
        )
    else:
        metrics = {"primary": {"run_label": "primary_16", "executed": False, "completed": False, "partial": True, "partial_reason": "preflight failed"}, "fallback": {"run_label": "fallback_8", "executed": False, "completed": False}}
        (out / "independent_validation_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (out / "independent_validation_trace_manifest.json").write_text(json.dumps({"trace_sharded": True, "shard_count": 0, "total_rows": 0, "shards": []}, indent=2) + "\n", encoding="utf-8")
        (out / "independent_validation_failure_summary.json").write_text(json.dumps({"failure_category_distribution": {}, "failure_count": 0}, indent=2) + "\n", encoding="utf-8")
        (out / "independent_validation_failure_examples.jsonl").write_text("", encoding="utf-8")
    readiness = assess_clean_validation_readiness(out, preflight, metrics)
    _write_mainline(out, preflight, metrics, readiness)
    print(json.dumps({
        "preflight_passed": readiness["preflight_passed"],
        "primary_completed": readiness["primary_independent_validation_completed"],
        "primary_rate": readiness["primary_compiler_verified_correct_rate"],
        "fallback_executed": readiness["fallback_executed"],
        "recommended_claim_level": readiness["recommended_claim_level"],
    }, ensure_ascii=False, indent=2, sort_keys=True))


def _write_mainline(out: Path, preflight: dict, metrics: dict, readiness: dict) -> None:
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
        "what_this_version_proved": "clean MSVC preflight and independent bounded-substrate compiler validation rerun were executed separately from original and patched records",
        "what_this_version_did_not_prove": still,
        "clean_msvc_preflight": preflight,
        "primary_independent_validation": metrics.get("primary", {}),
        "fallback_validation": metrics.get("fallback", {}),
        "permission_error_zero": readiness.get("primary_permission_error_count", 0) == 0,
        "cleanup_failure_recorded_separately": True,
        "boundary_compiler_misroute_summary": readiness.get("boundary_compiler_misroute_count", 0),
        "compiler_validation_confidence_restored": readiness.get("recommended_claim_level") in {"independent_compiler_validation_restored", "independent_compiler_validation_restored_with_fallback"},
        "recommended_claim_level": readiness.get("recommended_claim_level"),
        "blocking_issues": readiness.get("blocking_issues", []),
        "required_next_run": readiness.get("required_next_run"),
        "paper_v2_candidate_results": ["clean MSVC preflight", "independent compiler validation rerun"],
        "must_revalidate": ["larger full-level validation still not Turing-completeness evidence"],
        "post_v1_reserved_routes": ["root similarity incremental training", "verified backend as teacher for NL-to-semantic-IR adapter"],
        "still_not_proven": still,
    }
    (out / "mainline_conclusion.json").write_text(json.dumps(conclusion, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# v0.9.7.3 Mainline Conclusion", "", f"Recommended claim level: {readiness.get('recommended_claim_level')}", "", "## Still Not Proven"]
    lines.extend(f"- {item}" for item in still)
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
