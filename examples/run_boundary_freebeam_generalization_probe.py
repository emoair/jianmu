from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.boundary_generalization_metrics import compute_boundary_generalization_metrics
from jianmu.self_learning.darwinforge.freebeam_boundary_eval import FreeBeamConfig, load_training_probe_summary, run_freebeam_boundary_eval
from jianmu.self_learning.darwinforge.freebeam_rejection_diagnostics import diagnose_freebeam_rejection
from jianmu.self_learning.darwinforge.heldout_boundary_slices import build_heldout_boundary_slices, manifest_without_samples
from jianmu.self_learning.darwinforge.no_label_inference_guard import assert_no_label_fields_used


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_8_5_boundary_aware")
    parser.add_argument("--records-dir", default="records/v0_8_7")
    parser.add_argument("--source-training-records", default="records/v0_8_6")
    parser.add_argument("--scale", default="large", choices=["medium", "large"])
    parser.add_argument("--mode", default="quick", choices=["quick", "medium", "large"])
    parser.add_argument("--worker-count", type=int, default=4)
    parser.add_argument("--run-no-label-guard", default="true")
    parser.add_argument("--run-heldout-slices", default="true")
    parser.add_argument("--run-freebeam-eval", default="true")
    args = parser.parse_args()

    started = time.perf_counter()
    records_dir = Path(args.records_dir)
    records_dir.mkdir(parents=True, exist_ok=True)
    dataset_scale_dir = Path(args.dataset_dir) / args.scale
    config = FreeBeamConfig.for_mode(args.mode, worker_count=args.worker_count)
    training_summary = load_training_probe_summary(args.source_training_records)
    slice_result = build_heldout_boundary_slices(dataset_scale_dir, eval_limit=config.eval_limit)
    samples = slice_result["slices"]["heldout_mixed_boundary"]
    eval_result = run_freebeam_boundary_eval(samples, training_summary, config)
    guard = assert_no_label_fields_used(eval_result["feature_access"], str(records_dir / "inference_access_trace.jsonl"))
    metrics = compute_boundary_generalization_metrics(samples, eval_result["decisions"], training_summary)
    diagnostics = diagnose_freebeam_rejection(
        metrics,
        eval_result["decisions"],
        guard,
        {"real_promotion_enabled": False, "hardcoded_rejection_gate_added": False},
    )
    runtime = {"runtime_seconds": round(time.perf_counter() - started, 6), "worker_count": args.worker_count, "mode": args.mode}
    summary = {
        "mode": args.mode,
        "modes_attempted": [args.mode],
        "modes_completed": [args.mode],
        "dataset_scale_used": args.scale,
        "source_training_available": training_summary.get("available", False),
        "heldout_slice_counts": slice_result["heldout_slice_counts"],
        "heldout_leakage_check_passed": slice_result["leakage_check_passed"],
        "no_label_inference": guard,
        "metrics": metrics,
        "diagnostics": diagnostics,
        "real_promotion_enabled": False,
        "hardcoded_rejection_gate_added": False,
        "runtime": runtime,
    }
    _write_json(records_dir / "freebeam_boundary_metrics.json", summary)
    _write_json(records_dir / "heldout_slice_manifest.json", manifest_without_samples(slice_result))
    _write_json(records_dir / "no_label_inference_guard.json", guard)
    _write_json(records_dir / "boundary_generalization_metrics.json", metrics)
    _write_json(records_dir / "freebeam_rejection_diagnostics.json", diagnostics)
    _write_json(records_dir / "runtime_profile.json", runtime)
    _write_jsonl(records_dir / "freebeam_decisions.jsonl", eval_result["decisions"])
    _write_jsonl(records_dir / "false_accept_examples.jsonl", diagnostics["false_accept_examples"])
    _write_jsonl(records_dir / "false_reject_supported_examples.jsonl", diagnostics["false_reject_supported_examples"])
    _write_report(records_dir / "freebeam_boundary_report.md", summary)
    _write_mainline(records_dir, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_report(path: Path, summary: dict) -> None:
    m = summary["metrics"]
    d = summary["diagnostics"]
    path.write_text(
        "\n".join(
            [
                "# Boundary Free-Beam Generalization Probe（边界自由束泛化探针）",
                "",
                "## Source Training State（源训练状态）",
                f"- source_training_available: {summary['source_training_available']}",
                "",
                "## Held-Out Boundary Slices（保留边界切片）",
                f"- heldout_slice_counts: {summary['heldout_slice_counts']}",
                f"- leakage_check_passed: {summary['heldout_leakage_check_passed']}",
                "",
                "## No-Label Inference Guard（无标签推理防泄漏）",
                f"- no_label_inference_passed: {summary['no_label_inference']['no_label_inference_passed']}",
                f"- forbidden_field_access_count: {summary['no_label_inference']['forbidden_field_access_count']}",
                "",
                "## Free-Beam Boundary Metrics（自由束边界指标）",
                f"- current_supported_retention_rate: {m['current_supported_retention_rate']}",
                f"- hard_ood_rejection_rate: {m['hard_ood_rejection_rate']}",
                f"- true_false_accept_trap_rejection_rate: {m['true_false_accept_trap_rejection_rate']}",
                f"- future_domain_isolation_rate: {m['future_domain_isolation_rate']}",
                f"- near_ood_quarantine_rate: {m['near_ood_quarantine_rate']}",
                f"- overall_ood_false_accept_rate: {m['overall_ood_false_accept_rate']}",
                "",
                "## Comparison With v0.8.6 Probe（与 v0.8.6 探针对比）",
                f"- delta_ood_false_accept: {m.get('delta_ood_false_accept')}",
                f"- delta_current_supported_retention: {m.get('delta_current_supported_retention')}",
                "",
                "## Failure Examples（失败样例）",
                f"- false_accept_examples: {len(d['false_accept_examples'])}",
                f"- false_reject_supported_examples: {len(d['false_reject_supported_examples'])}",
                "",
                "## Rejection Diagnostics（拒绝诊断）",
                f"- freebeam_emergent_rejection_signal_confirmed: {d['freebeam_emergent_rejection_signal_confirmed']}",
                f"- partial_boundary_generalization: {d['partial_boundary_generalization']}",
                f"- boundary_probe_did_not_generalize: {d['boundary_probe_did_not_generalize']}",
                f"- over_rejection_detected: {d['over_rejection_detected']}",
                "",
                "## Updated Mainline Judgment（更新主线判断）",
                "This is a no-label free-beam probe, not a full-scale convergence claim.",
                "",
                "## Non-Claims（非主张）",
                "- This does not prove stable convergence.",
                "- This does not prove general program synthesis.",
                "- This does not prove solved arithmetic.",
                "- This does not prove OOD solved.",
                "- This does not prove a fully emergent rejection gate.",
                "- This does not prove advantage over same-size LLM.",
                "- This does not prove safe real promotion.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_mainline(records_dir: Path, summary: dict) -> None:
    m = summary["metrics"]
    d = summary["diagnostics"]
    ledger = {
        "proved": ["no-label guard passed", "held-out boundary slices evaluated"],
        "not_proved": [
            "stable convergence",
            "general program synthesis",
            "solved arithmetic",
            "OOD solved",
            "fully emergent rejection gate",
            "advantage over same-size LLM",
            "full-scale generalization",
            "safe real promotion",
        ],
        "new_bottleneck": "needs real router-state evaluation if probe-backed free-beam remains simulated",
        "changes_mainline_judgment": d["freebeam_emergent_rejection_signal_confirmed"],
        "next_minimal_action": "run medium/large free-beam evaluation with persisted trained branch state",
        "paper_relevance": ["no-label free-beam comparison table", "held-out boundary metrics"],
        "must_reproduce": ["medium scale", "real router state", "external held-out OOD slice"],
        "risk": {"pseudo_improvement": True, "negative_transfer": False, "ood_pollution": m["overall_ood_false_accept_rate"] > 0},
        "no_label_inference_passed": summary["no_label_inference"]["no_label_inference_passed"],
        "heldout_leakage_check_passed": summary["heldout_leakage_check_passed"],
        "current_supported_retention_rate": m["current_supported_retention_rate"],
        "hard_ood_rejection_rate": m["hard_ood_rejection_rate"],
        "true_false_accept_trap_rejection_rate": m["true_false_accept_trap_rejection_rate"],
        "future_domain_isolation_rate": m["future_domain_isolation_rate"],
        "near_ood_quarantine_rate": m["near_ood_quarantine_rate"],
        "overall_ood_false_accept_rate": m["overall_ood_false_accept_rate"],
        "freebeam_emergent_rejection_signal_confirmed": d["freebeam_emergent_rejection_signal_confirmed"],
        "partial_boundary_generalization": d["partial_boundary_generalization"],
        "boundary_probe_did_not_generalize": d["boundary_probe_did_not_generalize"],
        "over_rejection_detected": d["over_rejection_detected"],
        "hardcoded_rejection_gate_added": False,
        "real_promotion_enabled": False,
    }
    _write_json(records_dir / "mainline_conclusion.json", ledger)
    (records_dir / "mainline_conclusion.md").write_text(
        "\n".join(
            [
                "# v0.8.7 Mainline Conclusion（主线结论）",
                "",
                f"- no_label_inference_passed: {ledger['no_label_inference_passed']}",
                f"- heldout_leakage_check_passed: {ledger['heldout_leakage_check_passed']}",
                f"- freebeam_emergent_rejection_signal_confirmed: {ledger['freebeam_emergent_rejection_signal_confirmed']}",
                f"- overall_ood_false_accept_rate: {ledger['overall_ood_false_accept_rate']}",
                "- Still not proved: stable convergence, OOD solved, full-scale generalization, same-size LLM advantage, safe real promotion.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
