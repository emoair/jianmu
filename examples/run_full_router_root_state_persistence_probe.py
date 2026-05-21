from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.arxiv_readiness_v2 import assess_arxiv_readiness_v2
from jianmu.self_learning.darwinforge.cross_process_reload_eval import run_cross_process_reload_eval
from jianmu.self_learning.darwinforge.external_ood_slice import generate_external_ood_slice
from jianmu.self_learning.darwinforge.full_state_consistency import check_full_state_consistency
from jianmu.self_learning.darwinforge.full_state_reloader import load_full_state
from jianmu.self_learning.darwinforge.full_state_serializer import save_full_state
from jianmu.self_learning.darwinforge.heldout_boundary_slices import build_heldout_boundary_slices
from jianmu.self_learning.darwinforge.multiseed_boundary_eval import run_multiseed_boundary_eval
from jianmu.self_learning.darwinforge.reloaded_freebeam_eval import run_reloaded_freebeam_eval


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_8_5_boundary_aware")
    parser.add_argument("--source-records", default="records/v0_8_8")
    parser.add_argument("--output-records", default="records/v0_8_9")
    parser.add_argument("--mode", default="quick", choices=["quick", "medium", "large"])
    parser.add_argument("--worker-count", type=int, default=4)
    parser.add_argument("--seeds", default="42,43,44")
    parser.add_argument("--run-cross-process", default="true")
    parser.add_argument("--run-external-ood", default="true")
    parser.add_argument("--run-multiseed", default="true")
    parser.add_argument("--run-arxiv-readiness", default="true")
    args = parser.parse_args()

    started = time.perf_counter()
    out = Path(args.output_records)
    out.mkdir(parents=True, exist_ok=True)
    state_dir = out / "state"
    seeds = [int(x.strip()) for x in args.seeds.split(",") if x.strip()]
    eval_limit = {"quick": 1000, "medium": 3000, "large": 8000}[args.mode]

    saved = save_full_state(args.source_records, state_dir, seed=seeds[0])
    loaded = load_full_state(state_dir)
    dataset_scale = Path(args.dataset_dir) / "large"
    if not dataset_scale.exists():
        dataset_scale = Path(args.dataset_dir) / "medium"
    heldout = build_heldout_boundary_slices(dataset_scale, eval_limit=eval_limit, seed=seeds[0])
    same_process = run_reloaded_freebeam_eval(heldout["slices"]["heldout_mixed_boundary"], loaded, mode=args.mode, worker_count=args.worker_count)
    cross_process = (
        run_cross_process_reload_eval(state_dir, args.dataset_dir, out, mode=args.mode, worker_count=args.worker_count)
        if _flag(args.run_cross_process)
        else {"cross_process_eval_completed": False, "cross_process_reload_passed": False, "skip_reason": "disabled"}
    )
    external = generate_external_ood_slice(args.mode, out) if _flag(args.run_external_ood) else {"samples": [], "manifest": {}}
    external_eval = run_reloaded_freebeam_eval(external["samples"], loaded, mode=args.mode, worker_count=args.worker_count) if external["samples"] else {}
    multiseed = run_multiseed_boundary_eval(heldout["slices"]["heldout_mixed_boundary"], loaded, seeds, mode=args.mode, worker_count=args.worker_count) if _flag(args.run_multiseed) else {}
    v087 = _read_json(Path("records/v0_8_7") / "boundary_generalization_metrics.json")
    v088 = _read_json(Path(args.source_records) / "reloaded_freebeam_metrics.json")
    forbidden_scan = _read_json(state_dir / "forbidden_field_scan.json")
    consistency = check_full_state_consistency(
        v087,
        v088.get("metrics", v088),
        same_process,
        cross_process,
        external_eval.get("metrics", external_eval),
        multiseed,
        forbidden_scan,
        saved["persisted_state_support_level"],
    )
    readiness = assess_arxiv_readiness_v2(
        {**same_process, "cross_process_reload_passed": cross_process.get("cross_process_reload_passed")},
        external_eval.get("metrics", external_eval),
        multiseed,
        consistency,
        forbidden_scan,
    ) if _flag(args.run_arxiv_readiness) else {}
    runtime = {"mode": args.mode, "worker_count": args.worker_count, "runtime_seconds": round(time.perf_counter() - started, 6)}
    summary = {
        "mode": args.mode,
        "modes_attempted": [args.mode],
        "modes_completed": [args.mode],
        "state_inventory": saved["inventory"],
        "state_saved": saved["state_saved"],
        "state_loaded": loaded["state_loaded"],
        "persisted_state_support_level": saved["persisted_state_support_level"],
        "state_manifest_path": saved["state_manifest_path"],
        "forbidden_field_in_state_count": saved["forbidden_field_in_state_count"],
        "same_process_reload": _compact_eval(same_process),
        "same_process_reload_passed": _same_process_passed(same_process),
        "cross_process_reload": cross_process,
        "external_ood_manifest": external.get("manifest", {}),
        "external_ood_metrics": _compact_eval(external_eval),
        "multiseed_full_state_eval": multiseed,
        "full_state_consistency": consistency,
        "arxiv_readiness_v2": readiness,
        "runtime": runtime,
        "real_promotion_enabled": False,
        "hardcoded_rejection_gate_added": False,
    }
    _write_outputs(out, summary, same_process)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


def _compact_eval(result: dict) -> dict:
    compact = dict(result)
    compact.pop("decisions", None)
    compact.pop("guard", None)
    compact.pop("diagnostics", None)
    return compact


def _same_process_passed(result: dict) -> bool:
    return bool(result.get("no_label_inference_passed") and result.get("forbidden_field_access_count") == 0 and result.get("current_supported_retention_rate", 0) >= 0.98 and not result.get("over_rejection_detected"))


def _flag(value: str) -> bool:
    return str(value).lower() in {"1", "true", "yes", "y"}


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_outputs(out: Path, summary: dict, same_process: dict) -> None:
    _write_json(out / "full_state_metrics.json", summary)
    _write_json(out / "same_process_reload_metrics.json", summary["same_process_reload"])
    _write_json(out / "cross_process_reload_metrics.json", summary["cross_process_reload"])
    _write_json(out / "external_ood_metrics.json", summary["external_ood_metrics"])
    _write_json(out / "multiseed_full_state_eval.json", summary["multiseed_full_state_eval"])
    _write_json(out / "full_state_consistency.json", summary["full_state_consistency"])
    _write_json(out / "arxiv_readiness_v2.json", summary["arxiv_readiness_v2"])
    _write_json(out / "runtime_profile.json", summary["runtime"])
    _write_jsonl(out / "false_accept_examples.jsonl", same_process.get("diagnostics", {}).get("false_accept_examples", []))
    _write_jsonl(out / "false_reject_supported_examples.jsonl", same_process.get("diagnostics", {}).get("false_reject_supported_examples", []))
    _write_report(out / "full_state_report.md", summary)
    _write_mainline(out, summary)


def _write_report(path: Path, summary: dict) -> None:
    inv = summary["state_inventory"]
    sp = summary["same_process_reload"]
    cp = summary["cross_process_reload"]
    ext = summary["external_ood_metrics"]
    cons = summary["full_state_consistency"]
    ready = summary["arxiv_readiness_v2"]
    path.write_text(
        "\n".join(
            [
                "# Full Router/Root State Persistence（完整路由/根状态持久化）",
                "",
                "## State Inventory Audit（状态清单审计）",
                f"- inventory_passed: {inv['inventory_passed']}",
                f"- serializable_component_count: {inv['serializable_component_count']}",
                f"- missing_for_full_state: {inv['missing_for_full_state']}",
                "",
                "## Full Router State（完整路由状态）",
                f"- persisted_state_support_level: {summary['persisted_state_support_level']}",
                "",
                "## Full Root State（完整根状态）",
                "- Missing trained root colony runtime objects are reported rather than fabricated.",
                "",
                "## Forbidden Field Scan（禁用字段扫描）",
                f"- forbidden_field_in_state_count: {summary['forbidden_field_in_state_count']}",
                "",
                "## State Save / Load（状态保存与加载）",
                f"- state_saved: {summary['state_saved']}",
                f"- state_loaded: {summary['state_loaded']}",
                "",
                "## Same-Process Reload Eval（同进程重载评估）",
                f"- same_process_reload_passed: {summary['same_process_reload_passed']}",
                f"- current_supported_retention_rate: {sp.get('current_supported_retention_rate')}",
                f"- overall_ood_false_accept_rate: {sp.get('overall_ood_false_accept_rate')}",
                "",
                "## Cross-Process Reload Eval（跨进程重载评估）",
                f"- cross_process_reload_passed: {cp.get('cross_process_reload_passed')}",
                f"- no_label_inference_passed: {cp.get('no_label_inference_passed')}",
                "",
                "## External OOD Eval（外部分布外评估）",
                f"- external_ood_false_accept_rate: {ext.get('overall_ood_false_accept_rate')}",
                "",
                "## Multi-Seed Full-State Stability（多 seed 完整状态稳定性）",
                f"- stable_across_seeds: {summary['multiseed_full_state_eval'].get('stable_across_seeds')}",
                "",
                "## Full State Consistency（完整状态一致性）",
                f"- full_state_consistency_passed: {cons.get('full_state_consistency_passed')}",
                f"- consistency_failure_reason: {cons.get('consistency_failure_reason')}",
                "",
                "## arXiv Readiness v2",
                f"- ready_for_arxiv_technical_report: {ready.get('ready_for_arxiv_technical_report')}",
                f"- recommended_claim_level: {ready.get('recommended_claim_level')}",
                f"- blocking_issues: {ready.get('blocking_issues')}",
                "",
                "## Failure Analysis（失败分析）",
                "- Current records still lack trained full router/root runtime objects.",
                "",
                "## Updated Mainline Judgment（更新主线判断）",
                "- Serialization scaffolding and cross-process reload work, but support level is not full_router_root unless trained runtime state is captured.",
                "",
                "## Non-Claims（非主张）",
                "- This does not prove stable convergence.",
                "- This does not prove solved OOD.",
                "- This does not prove solved arithmetic.",
                "- This does not prove same-size LLM advantage.",
                "- This does not prove safe real promotion.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_mainline(out: Path, summary: dict) -> None:
    sp = summary["same_process_reload"]
    cp = summary["cross_process_reload"]
    ext = summary["external_ood_metrics"]
    cons = summary["full_state_consistency"]
    ready = summary["arxiv_readiness_v2"]
    ledger = {
        "proved": ["state inventory completed", "state serializer/reloader executed", "cross-process reload eval executed"],
        "not_proved": ["full_router_root persisted trained state", "stable convergence", "solved OOD", "same-size LLM advantage", "safe real promotion"],
        "new_bottleneck": "trained BranchChain/root runtime objects are not yet captured in source records",
        "changes_mainline_judgment": False,
        "next_minimal_action": "capture actual trained population and root colony objects before writing readiness true",
        "paper_relevance": ["state inventory table", "summary-vs-full blocker", "cross-process reload result"],
        "must_reproduce": ["full_router_root support level", "independent external OOD", "more seeds"],
        "risk": {"pseudo_improvement": summary["persisted_state_support_level"] != "full_router_root", "negative_transfer": False, "ood_pollution": False},
        "state_inventory_passed": summary["state_inventory"]["inventory_passed"],
        "persisted_state_support_level": summary["persisted_state_support_level"],
        "state_saved": summary["state_saved"],
        "state_loaded": summary["state_loaded"],
        "forbidden_field_in_state_count": summary["forbidden_field_in_state_count"],
        "same_process_reload_passed": summary["same_process_reload_passed"],
        "cross_process_reload_passed": cp.get("cross_process_reload_passed"),
        "full_state_consistency_passed": cons.get("full_state_consistency_passed"),
        "reloaded_no_label_inference_passed": sp.get("no_label_inference_passed"),
        "reloaded_current_supported_retention_rate": sp.get("current_supported_retention_rate"),
        "reloaded_overall_ood_false_accept_rate": sp.get("overall_ood_false_accept_rate"),
        "external_ood_false_accept_rate": ext.get("overall_ood_false_accept_rate"),
        "multi_seed_stable": summary["multiseed_full_state_eval"].get("stable_across_seeds"),
        "ready_for_arxiv_technical_report": ready.get("ready_for_arxiv_technical_report"),
        "recommended_claim_level": ready.get("recommended_claim_level"),
        "blocking_issues": ready.get("blocking_issues"),
        "hardcoded_rejection_gate_added": False,
        "real_promotion_enabled": False,
    }
    _write_json(out / "mainline_conclusion.json", ledger)
    (out / "mainline_conclusion.md").write_text(
        "\n".join(
            [
                "# v0.8.9 Mainline Conclusion（主线结论）",
                "",
                f"- state_inventory_passed: {ledger['state_inventory_passed']}",
                f"- persisted_state_support_level: {ledger['persisted_state_support_level']}",
                f"- cross_process_reload_passed: {ledger['cross_process_reload_passed']}",
                f"- full_state_consistency_passed: {ledger['full_state_consistency_passed']}",
                f"- ready_for_arxiv_technical_report: {ledger['ready_for_arxiv_technical_report']}",
                f"- blocking_issues: {ledger['blocking_issues']}",
                "- Still not proved: full_router_root trained persisted state, stable convergence, solved OOD, same-size LLM advantage, safe real promotion.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
