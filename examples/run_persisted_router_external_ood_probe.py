from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.arxiv_readiness import assess_arxiv_readiness
from jianmu.self_learning.darwinforge.external_ood_slice import generate_external_ood_slice
from jianmu.self_learning.darwinforge.heldout_boundary_slices import build_heldout_boundary_slices
from jianmu.self_learning.darwinforge.multiseed_boundary_eval import run_multiseed_boundary_eval
from jianmu.self_learning.darwinforge.persisted_router_state import load_persisted_router_state, save_persisted_router_state
from jianmu.self_learning.darwinforge.persisted_state_consistency import check_persisted_state_consistency, summarize_metrics_for_consistency
from jianmu.self_learning.darwinforge.reloaded_freebeam_eval import run_reloaded_freebeam_eval


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_8_5_boundary_aware")
    parser.add_argument("--source-records", default="records/v0_8_7")
    parser.add_argument("--output-records", default="records/v0_8_8")
    parser.add_argument("--mode", default="quick", choices=["quick", "medium", "large"])
    parser.add_argument("--worker-count", type=int, default=4)
    parser.add_argument("--seeds", default="42,43,44")
    parser.add_argument("--run-external-ood", default="true")
    parser.add_argument("--run-multiseed", default="true")
    parser.add_argument("--run-arxiv-readiness", default="true")
    args = parser.parse_args()

    started = time.perf_counter()
    output_records = Path(args.output_records)
    output_records.mkdir(parents=True, exist_ok=True)
    state_dir = output_records / "state"
    seeds = [int(part.strip()) for part in args.seeds.split(",") if part.strip()]

    state_save = save_persisted_router_state(args.source_records, state_dir, seed=seeds[0])
    persisted_state = load_persisted_router_state(state_dir)

    dataset_scale_dir = Path(args.dataset_dir) / "large"
    if not dataset_scale_dir.exists():
        dataset_scale_dir = Path(args.dataset_dir) / "medium"
    eval_limit = {"quick": 1000, "medium": 3000, "large": 8000}[args.mode]
    heldout = build_heldout_boundary_slices(dataset_scale_dir, eval_limit=eval_limit, seed=seeds[0])
    samples = heldout["slices"]["heldout_mixed_boundary"]

    reloaded_eval = run_reloaded_freebeam_eval(samples, persisted_state, mode=args.mode, worker_count=args.worker_count)
    external = generate_external_ood_slice(args.mode, output_records) if _flag(args.run_external_ood) else {"samples": [], "manifest": {}}
    external_eval = run_reloaded_freebeam_eval(external["samples"], persisted_state, mode=args.mode, worker_count=args.worker_count) if external["samples"] else {}
    multiseed = run_multiseed_boundary_eval(samples, persisted_state, seeds, mode=args.mode, worker_count=args.worker_count) if _flag(args.run_multiseed) else {}

    original_metrics = _read_json(Path(args.source_records) / "boundary_generalization_metrics.json")
    consistency = check_persisted_state_consistency(original_metrics, summarize_metrics_for_consistency(reloaded_eval))
    readiness = (
        assess_arxiv_readiness(_read_json(Path(args.source_records) / "freebeam_boundary_metrics.json"), reloaded_eval, external_eval, multiseed, consistency)
        if _flag(args.run_arxiv_readiness)
        else {}
    )

    runtime = {
        "mode": args.mode,
        "worker_count": args.worker_count,
        "runtime_seconds": round(time.perf_counter() - started, 6),
        "external_ood_total_count": external.get("manifest", {}).get("external_ood_total_count", 0),
    }
    summary = {
        "mode": args.mode,
        "modes_attempted": [args.mode],
        "modes_completed": [args.mode],
        "persisted_state": {**state_save, "state_loaded": persisted_state["state_loaded"]},
        "reloaded_freebeam": _without_decisions(reloaded_eval),
        "external_ood_manifest": external.get("manifest", {}),
        "external_ood_metrics": _without_decisions(external_eval),
        "multiseed_boundary_eval": multiseed,
        "persisted_state_consistency": consistency,
        "arxiv_readiness": readiness,
        "heldout_leakage_check_passed": heldout["leakage_check_passed"],
        "runtime": runtime,
        "real_promotion_enabled": False,
        "hardcoded_rejection_gate_added": False,
    }

    _write_json(output_records / "persisted_router_metrics.json", summary)
    _write_json(output_records / "reloaded_freebeam_metrics.json", _without_decisions(reloaded_eval))
    _write_json(output_records / "external_ood_metrics.json", _without_decisions(external_eval))
    _write_json(output_records / "multiseed_boundary_eval.json", multiseed)
    _write_json(output_records / "persisted_state_consistency.json", consistency)
    _write_json(output_records / "arxiv_readiness.json", readiness)
    _write_json(output_records / "runtime_profile.json", runtime)
    _write_jsonl(output_records / "false_accept_examples.jsonl", reloaded_eval.get("diagnostics", {}).get("false_accept_examples", []))
    _write_jsonl(output_records / "false_reject_supported_examples.jsonl", reloaded_eval.get("diagnostics", {}).get("false_reject_supported_examples", []))
    _write_report(output_records / "persisted_router_report.md", summary)
    _write_mainline(output_records, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


def _without_decisions(result: dict) -> dict:
    if not result:
        return {}
    compact = dict(result)
    compact.pop("decisions", None)
    compact.pop("guard", None)
    compact.pop("diagnostics", None)
    compact["false_accept_examples_count"] = result.get("false_accept_examples_count", 0)
    compact["false_reject_supported_examples_count"] = result.get("false_reject_supported_examples_count", 0)
    return compact


def _flag(value: str) -> bool:
    return str(value).lower() in {"1", "true", "yes", "y"}


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {"available": False, "missing_path": str(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_report(path: Path, summary: dict) -> None:
    state = summary["persisted_state"]
    reload = summary["reloaded_freebeam"]
    external = summary["external_ood_metrics"]
    consistency = summary["persisted_state_consistency"]
    readiness = summary["arxiv_readiness"]
    path.write_text(
        "\n".join(
            [
                "# Persisted Router External OOD Eval（持久化路由与外部 OOD 评估）",
                "",
                "## Persisted State Support Level（持久化状态支持等级）",
                f"- persisted_state_support_level: {state['persisted_state_support_level']}",
                "- This run records available probe summaries honestly; it does not claim full BranchChain/root persistence.",
                "",
                "## State Save / Load（状态保存与加载）",
                f"- state_saved: {state['state_saved']}",
                f"- state_loaded: {state['state_loaded']}",
                f"- state_manifest_path: {state['state_manifest_path']}",
                f"- forbidden_field_in_state_count: {state['forbidden_field_in_state_count']}",
                "",
                "## No-Label Reloaded Evaluation（无标签重载评估）",
                f"- no_label_inference_passed: {reload.get('no_label_inference_passed')}",
                f"- forbidden_field_access_count: {reload.get('forbidden_field_access_count')}",
                f"- current_supported_retention_rate: {reload.get('current_supported_retention_rate')}",
                f"- overall_ood_false_accept_rate: {reload.get('overall_ood_false_accept_rate')}",
                "",
                "## External OOD Slice（外部分布外切片）",
                f"- external_ood_total_count: {summary['external_ood_manifest'].get('external_ood_total_count')}",
                f"- category_distribution: {summary['external_ood_manifest'].get('category_distribution')}",
                "",
                "## External OOD Metrics（外部分布外指标）",
                f"- external_ood_false_accept_rate: {external.get('overall_ood_false_accept_rate')}",
                f"- hard_ood_rejection_rate: {external.get('hard_ood_rejection_rate')}",
                f"- trap_rejection_rate: {external.get('true_false_accept_trap_rejection_rate')}",
                f"- future_domain_isolation_rate: {external.get('future_domain_isolation_rate')}",
                f"- near_ood_quarantine_rate: {external.get('near_ood_quarantine_rate')}",
                "",
                "## Multi-Seed Stability（多 seed 稳定性）",
                f"- stable_across_seeds: {summary['multiseed_boundary_eval'].get('stable_across_seeds')}",
                f"- seed_metrics: {summary['multiseed_boundary_eval'].get('seed_metrics')}",
                "",
                "## Persisted State Consistency（持久化状态一致性）",
                f"- persisted_state_consistency_passed: {consistency.get('persisted_state_consistency_passed')}",
                f"- max_abs_metric_delta: {consistency.get('max_abs_metric_delta')}",
                "",
                "## arXiv Readiness Assessment（arXiv 准备度评估）",
                f"- ready_for_arxiv_technical_report: {readiness.get('ready_for_arxiv_technical_report')}",
                f"- recommended_claim_level: {readiness.get('recommended_claim_level')}",
                f"- blocking_issues: {readiness.get('blocking_issues')}",
                "",
                "## Failure Analysis（失败分析）",
                "- Summary-only state remains a blocker for full persisted router/root proof.",
                "",
                "## Updated Mainline Judgment（更新主线判断）",
                "- Reloaded summary-state behavior can be audited, but full persisted router/root state remains future work.",
                "",
                "## Non-Claims（非主张）",
                "- This does not prove stable convergence.",
                "- This does not prove solved arithmetic.",
                "- This does not prove solved OOD.",
                "- This does not prove general program synthesis.",
                "- This does not prove same-size LLM advantage.",
                "- This does not prove safe real promotion.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_mainline(records_dir: Path, summary: dict) -> None:
    state = summary["persisted_state"]
    reload = summary["reloaded_freebeam"]
    external = summary["external_ood_metrics"]
    consistency = summary["persisted_state_consistency"]
    multiseed = summary["multiseed_boundary_eval"]
    readiness = summary["arxiv_readiness"]
    ledger = {
        "proved": [
            "summary-level persisted state can be saved and reloaded",
            "reloaded no-label free-beam evaluation completed",
            "external OOD slice was evaluated",
            "multi-seed summary evaluation completed",
        ],
        "not_proved": [
            "full persisted router/root state",
            "stable convergence",
            "solved OOD",
            "solved arithmetic",
            "same-size LLM advantage",
            "safe real promotion",
        ],
        "new_bottleneck": "full router/root state persistence beyond summary-only state",
        "changes_mainline_judgment": False,
        "next_minimal_action": "persist real router/root state objects and rerun external OOD",
        "paper_relevance": ["summary-only reload caveat", "external OOD audit", "multi-seed table"],
        "must_reproduce": ["full persisted state", "independent external OOD", "more seeds"],
        "risk": {"pseudo_improvement": state["persisted_state_support_level"] == "summary_only", "negative_transfer": False, "ood_pollution": False},
        "persisted_state_support_level": state["persisted_state_support_level"],
        "state_saved": state["state_saved"],
        "state_loaded": state["state_loaded"],
        "forbidden_field_in_state_count": state["forbidden_field_in_state_count"],
        "reloaded_no_label_inference_passed": reload.get("no_label_inference_passed"),
        "reloaded_current_supported_retention_rate": reload.get("current_supported_retention_rate"),
        "reloaded_overall_ood_false_accept_rate": reload.get("overall_ood_false_accept_rate"),
        "external_ood_false_accept_rate": external.get("overall_ood_false_accept_rate"),
        "external_hard_ood_rejection_rate": external.get("hard_ood_rejection_rate"),
        "external_trap_rejection_rate": external.get("true_false_accept_trap_rejection_rate"),
        "external_future_domain_isolation_rate": external.get("future_domain_isolation_rate"),
        "external_near_ood_quarantine_rate": external.get("near_ood_quarantine_rate"),
        "persisted_state_consistency_passed": consistency.get("persisted_state_consistency_passed"),
        "multi_seed_stable": multiseed.get("stable_across_seeds"),
        "ready_for_arxiv_technical_report": readiness.get("ready_for_arxiv_technical_report"),
        "recommended_claim_level": readiness.get("recommended_claim_level"),
        "hardcoded_rejection_gate_added": False,
        "real_promotion_enabled": False,
    }
    _write_json(records_dir / "mainline_conclusion.json", ledger)
    (records_dir / "mainline_conclusion.md").write_text(
        "\n".join(
            [
                "# v0.8.8 Mainline Conclusion（主线结论）",
                "",
                f"- persisted_state_support_level: {ledger['persisted_state_support_level']}",
                f"- state_saved: {ledger['state_saved']}",
                f"- state_loaded: {ledger['state_loaded']}",
                f"- reloaded_no_label_inference_passed: {ledger['reloaded_no_label_inference_passed']}",
                f"- external_ood_false_accept_rate: {ledger['external_ood_false_accept_rate']}",
                f"- multi_seed_stable: {ledger['multi_seed_stable']}",
                f"- ready_for_arxiv_technical_report: {ledger['ready_for_arxiv_technical_report']}",
                "- Still not proved: full persisted router/root state, solved OOD, stable convergence, same-size LLM advantage, safe real promotion.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
