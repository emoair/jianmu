from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.bounded_substrate_full_readiness import assess_bounded_substrate_full_readiness
from jianmu.self_learning.darwinforge.bounded_substrate_full_rerun import run_bounded_substrate_full_rerun
from jianmu.self_learning.darwinforge.bounded_substrate_signal_audit import run_bounded_substrate_signal_audit
from jianmu.self_learning.darwinforge.bounded_substrate_worker_scaling import run_bounded_substrate_worker_scaling


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_9_6_turing_substrate_curriculum")
    parser.add_argument("--source-records", default="records/v0_9_7")
    parser.add_argument("--output-records", default="records/v0_9_7_1")
    parser.add_argument("--modes", default="audit,quick-full")
    parser.add_argument("--seeds", default="56")
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--worker-levels", default="8,16,32,64")
    parser.add_argument("--beam-size", type=int, default=8)
    parser.add_argument("--run-cross-process", default="true")
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--max-runtime-hours", type=float, default=1.0)
    parser.add_argument("--checkpoint-interval-minutes", type=int, default=15)
    parser.add_argument("--timeout-seconds", type=int, default=5)
    args = parser.parse_args()
    modes = {part.strip() for part in args.modes.split(",") if part.strip()}
    seeds = [int(part) for part in args.seeds.split(",") if part.strip()]
    out = Path(args.output_records)
    out.mkdir(parents=True, exist_ok=True)
    signal = run_bounded_substrate_signal_audit(args.source_records, args.dataset_dir, out)
    if "quick-full" in modes:
        full_modes = ["quick-full"]
    elif "full-rerun" in modes:
        full_modes = ["full-probe"]
    else:
        full_modes = []
    if full_modes:
        full = run_bounded_substrate_full_rerun(
            args.dataset_dir,
            out,
            full_modes,
            seeds,
            args.compile_worker_count,
            args.beam_size,
            args.run_cross_process.lower() == "true",
            args.run_compiler_validation.lower() == "true",
            args.timeout_seconds,
        )
    else:
        full = {}
    if "worker-scaling" in modes:
        worker = run_bounded_substrate_worker_scaling(
            args.dataset_dir,
            out,
            [int(part) for part in args.worker_levels.split(",") if part.strip()],
            seed=59,
            timeout_seconds=args.timeout_seconds,
        )
    else:
        worker = {"worker_scaling_completed": False, "best_worker_count_for_bounded_substrate": args.compile_worker_count, "recommended_default_worker_count": args.compile_worker_count, "by_worker_level": {}}
    readiness = assess_bounded_substrate_full_readiness(out, signal, full, worker)
    _write_mainline(out, signal, full, worker, readiness)
    print(json.dumps({
        "signal_audit_passed": signal.get("signal_audit_passed"),
        "full_rerun_completed": readiness.get("full_rerun_completed"),
        "full_rerun_partial": readiness.get("full_rerun_partial"),
        "supported_candidate_hit_before": full.get("supported_candidate_hit_before"),
        "supported_candidate_hit_after": full.get("supported_candidate_hit_after"),
        "top1_before": full.get("top1_supported_correct_before"),
        "top1_after": full.get("top1_supported_correct_after"),
        "best_worker_count_for_bounded_substrate": worker.get("best_worker_count_for_bounded_substrate"),
        "recommended_claim_level": readiness.get("recommended_claim_level"),
    }, ensure_ascii=False, indent=2, sort_keys=True))


def _write_mainline(out: Path, signal: dict, full: dict, worker: dict, readiness: dict) -> None:
    compiler = _read_json(out / "compiler_validation_metrics.json")
    stage = _read_json(out / "full_stage_metrics.json")
    conclusion = {
        "what_this_version_proved": "v0.9.7 signal audit and bounded full-level rerun were executed with per-sample provenance and real compiler validation",
        "what_this_version_did_not_prove": _still_not_proven(),
        "v0_9_7_signal_audit_conclusion": signal.get("signal_audit_passed", False),
        "full_level_rerun_completed": readiness.get("full_rerun_completed", False),
        "full_level_rerun_partial": readiness.get("full_rerun_partial", False),
        "full_level_before_after": {
            "candidate_hit": [full.get("supported_candidate_hit_before"), full.get("supported_candidate_hit_after")],
            "correct_output_in_beam": [full.get("correct_output_in_beam_before"), full.get("correct_output_in_beam_after")],
            "top1": [full.get("top1_supported_correct_before"), full.get("top1_supported_correct_after")],
        },
        "stage_success_summary": {k: v.get("top1_correct_after") for k, v in stage.get("by_stage", {}).items()},
        "compiler_validation_summary": {
            "backend_type": compiler.get("backend_type"),
            "compiler_name": compiler.get("compiler_name"),
            "compile_worker_count": compiler.get("compile_worker_count"),
            "real_compiler_invocation_count": compiler.get("real_compiler_invocation_count"),
            "compiler_verified_correct_rate": compiler.get("compiler_verified_correct_rate"),
            "boundary_compiler_misroute_count": compiler.get("boundary_compiler_misroute_count"),
        },
        "worker_scaling_summary": worker,
        "best_worker_count_for_bounded_substrate": worker.get("best_worker_count_for_bounded_substrate"),
        "boundary_false_accept_summary": {
            "unsupported": full.get("unsupported_false_accept_rate", 0.0),
            "trap": full.get("trap_false_accept_rate", 0.0),
            "future": full.get("future_domain_supported_accept_rate", 0.0),
            "near_ood": full.get("near_ood_supported_accept_rate", 0.0),
            "hard_ood": full.get("hard_ood_false_accept_rate", 0.0),
        },
        "baseline_ablation_summary": _read_json(out / "bounded_substrate_baseline_ablation.json"),
        "forbidden_field_leakage_summary": _read_json(out / "leakage_audit.json"),
        "full_router_root_cross_process_reload_summary": _read_json(out / "cross_process_trace.json") or _read_json(out / "bounded_substrate_cross_process_trace.json"),
        "recommended_claim_level": readiness.get("recommended_claim_level"),
        "blocking_issues": readiness.get("blocking_issues", []),
        "required_next_run": readiness.get("required_next_run"),
        "paper_v2_candidate_results": ["per-sample signal audit", "full-level bounded substrate rerun", "8/16/32/64 worker scaling"],
        "must_revalidate": ["larger independent full-level run", "no Turing-completeness claim"],
        "post_v1_reserved_routes": ["root similarity incremental training", "verified backend as teacher for NL-to-semantic-IR adapter"],
        "still_not_proven": _still_not_proven(),
    }
    (out / "mainline_conclusion.json").write_text(json.dumps(conclusion, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# v0.9.7.1 Mainline Conclusion", "", f"Recommended claim level: {conclusion['recommended_claim_level']}", "", "## Still Not Proven"]
    lines.extend(f"- {item}" for item in _still_not_proven())
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _still_not_proven() -> list[str]:
    return [
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


if __name__ == "__main__":
    main()
