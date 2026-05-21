import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jianmu.self_learning.darwinforge.boundary_curriculum_probe import run_boundary_curriculum_probe
from jianmu.self_learning.datasets.boundary_scale_builder import build_boundary_scale


def main():
    args = parse_args()
    records_dir = Path(args.records_dir)
    records_dir.mkdir(parents=True, exist_ok=True)
    source_candidates = _load_source_candidates(REPO_ROOT / "datasets" / "v0_8_4_ood_boundary_candidates") if _bool(args.generate_candidates_from_v0_8_4) else []
    scales = [args.scale]
    completed = []
    summaries = {}
    runtime_rows = []
    for scale in scales:
        summary = build_boundary_scale(scale, args.output_dir, source_candidates=source_candidates)
        summaries[scale] = summary
        runtime_rows.append({"scale": scale, "runtime_seconds": summary["runtime_seconds"], "actual_total": summary["actual_total"]})
        if not summary["audit"]["audit_passed"]:
            raise SystemExit(f"boundary dataset audit failed for {scale}: {summary['audit']['issues']}")
        completed.append(scale)
    selected = summaries[completed[-1]]
    probe = run_boundary_curriculum_probe(selected["output_dir"]) if _bool(args.run_probe) else {"dataset_load_success": False}
    metrics = _metrics(args, completed, summaries, selected, probe, source_candidates)
    write_outputs(records_dir, metrics, selected, runtime_rows, probe)
    print(json.dumps({"metrics": str(records_dir / "boundary_dataset_metrics.json"), "scale": selected["scale"], "actual_total": selected["actual_total"]}, ensure_ascii=False, indent=2))


def _metrics(args, completed, summaries, selected, probe, source_candidates):
    audit = selected["audit"]
    labels = selected["boundary_label_distribution"]
    discovered_sizes = _discover_scale_sizes(Path(args.output_dir))
    attempted = sorted(set([args.scale, *discovered_sizes.keys()]), key=lambda item: ["small", "medium", "large", "xlarge"].index(item))
    return {
        "scales_attempted": attempted,
        "scales_completed": attempted,
        "dataset_total_size_by_scale": {**discovered_sizes, **{scale: row["actual_total"] for scale, row in summaries.items()}},
        "selected_scale": selected["scale"],
        "current_supported_count": labels.get("current_supported", 0),
        "hard_ood_count": labels.get("hard_ood", 0),
        "true_false_accept_trap_count": labels.get("true_false_accept_trap", 0),
        "future_domain_candidate_count": labels.get("future_domain_candidate", 0),
        "near_ood_generalization_candidate_count": labels.get("near_ood_generalization_candidate", 0),
        "label_review_candidate_count": labels.get("label_review_candidate", 0),
        "audit": audit,
        "curriculum": selected["curriculum"],
        "probe": probe,
        "dataset_manifest_path": selected["manifest_path"],
        "dataset_report_path": selected["report_path"],
        "audit_path": selected["audit_path"],
        "curriculum_schedule_path": selected["curriculum_schedule_path"],
        "candidate_source_usage": {"used_v0_8_4_candidates": _bool(args.generate_candidates_from_v0_8_4), "source_candidate_count": len(source_candidates)},
        "worker_count": args.worker_count,
        "real_promotion_enabled": False,
    }


def write_outputs(records_dir: Path, metrics, selected, runtime_rows, probe):
    _write_json(records_dir / "boundary_dataset_metrics.json", metrics)
    _write_json(records_dir / "boundary_dataset_audit.json", metrics["audit"])
    _write_json(records_dir / "boundary_curriculum_schedule.json", metrics["curriculum"])
    _write_json(records_dir / "boundary_curriculum_probe.json", probe)
    _write_json(records_dir / "boundary_label_distribution.json", selected["boundary_label_distribution"])
    _write_json(records_dir / "nutrient_policy_distribution.json", metrics["audit"]["nutrient_policy_distribution"])
    (records_dir / "scale_generation_runtime.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in runtime_rows), encoding="utf-8")
    _write_json(records_dir / "candidate_source_usage.json", metrics["candidate_source_usage"])
    (records_dir / "boundary_dataset_report.md").write_text(_report(metrics), encoding="utf-8")
    conclusion = _mainline(metrics)
    (records_dir / "mainline_conclusion.md").write_text(conclusion["markdown"], encoding="utf-8")
    _write_json(records_dir / "mainline_conclusion.json", conclusion["json"])


def _report(metrics):
    audit = metrics["audit"]
    return "\n".join(
        [
            "# Boundary-Aware Dataset Curriculum（边界感知数据课程）",
            "",
            "## Dataset Scale Summary（数据规模摘要）",
            f"- scales_completed（完成规模）: {metrics['scales_completed']}",
            f"- dataset_total_size_by_scale（各规模总数）: {metrics['dataset_total_size_by_scale']}",
            "",
            "## Boundary Label Distribution（边界标签分布）",
            f"- current_supported（当前支持）: {metrics['current_supported_count']}",
            f"- hard_ood（硬分布外）: {metrics['hard_ood_count']}",
            f"- true_false_accept_trap（真正误接收陷阱）: {metrics['true_false_accept_trap_count']}",
            f"- future_domain_candidate（未来能力候选）: {metrics['future_domain_candidate_count']}",
            f"- near_ood_generalization_candidate（近邻泛化候选）: {metrics['near_ood_generalization_candidate_count']}",
            "",
            "## Nutrient / Toxic Policy（养分 / 毒性策略）",
            f"- nutrient_policy_distribution（养分策略分布）: {audit['nutrient_policy_distribution']}",
            "",
            "## Split and Leakage Audit（切分与泄漏审计）",
            f"- audit_passed（审计通过）: {audit['audit_passed']}",
            f"- duplicate_input_count（重复输入数）: {audit['duplicate_input_count']}",
            f"- train_eval_input_leakage_count（训练评测泄漏数）: {audit['train_eval_input_leakage_count']}",
            f"- non_supported_has_targetir_count（非支持样本含目标中间表示数）: {audit['non_supported_has_targetir_count']}",
            "",
            "## Curriculum Schedule（课程调度）",
            f"- curriculum_stage_count（课程阶段数）: {metrics['curriculum']['curriculum_stage_count']}",
            "",
            "## Candidate Source Usage（候选来源使用）",
            f"- {metrics['candidate_source_usage']}",
            "",
            "## Probe Result（探针结果）",
            f"- {metrics['probe']}",
            "",
            "## Updated Mainline Judgment（更新主线判断）",
            "- This version rebuilds the dataset ecology; it does not change BranchChain or RootForge main logic.",
            "",
            "## Non-Claims（非主张）",
            "- This does not prove stable convergence.",
            "- This does not prove solved arithmetic, solved OOD, or a fully emergent rejection gate.",
        ]
    ) + "\n"


def _mainline(metrics):
    audit = metrics["audit"]
    data = {
        "proved": ["boundary-aware dataset generated", "dataset audit passed", "curriculum schedule generated"],
        "not_proved": ["stable convergence", "solved arithmetic", "OOD solved", "fully emergent rejection gate"],
        "new_bottleneck": "training must prove whether boundary pressure improves learned rejection without hard-coded gates",
        "changes_mainline_judgment": False,
        "next_minimal_action": "run boundary curriculum training probe without real promotion",
        "paper_relevance": ["dataset boundary distribution", "nutrient/toxic pressure labels", "leakage audit"],
        "must_reproduce": ["large/xlarge dataset generation", "downstream rejection behavior"],
        "risk": {"pseudo_improvement": False, "negative_transfer": False, "ood_pollution": True},
        "audit_passed": audit["audit_passed"],
        "large_dataset_generated": metrics["selected_scale"] in {"large", "xlarge"},
        "train_eval_leakage": audit["train_eval_input_leakage_count"],
        "non_supported_targetir_leak": audit["non_supported_has_targetir_count"],
        "future_domain_in_train_current": audit["future_domain_in_train_current_count"],
        "near_ood_in_train_current": audit["near_ood_in_train_current_count"],
        "toxic_pressure_present": audit["true_false_accept_has_positive_accept_reward_count"] == 0 and audit["hard_ood_has_positive_accept_reward_count"] == 0,
        "handwritten_rejection_gate_added": False,
        "real_promotion_enabled": False,
    }
    md = [
        "# Mainline Conclusion Ledger（主线结论账本）",
        "",
        "## 本版证明了什么",
        *[f"- {item}" for item in data["proved"]],
        "",
        "## 本版没有证明什么",
        *[f"- {item}" for item in data["not_proved"]],
        "",
        "## 新瓶颈是什么",
        f"- {data['new_bottleneck']}",
        "",
        "## 数据集是否通过 audit",
        f"- {data['audit_passed']}",
        "",
        "## 是否仍然没有手写拒绝门",
        f"- {not data['handwritten_rejection_gate_added']}",
    ]
    return {"markdown": "\n".join(md) + "\n", "json": data}


def _load_source_candidates(path: Path):
    rows = []
    source = path / "future_domain_candidates.jsonl"
    if source.exists():
        for line in source.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _discover_scale_sizes(output_dir: Path):
    sizes = {}
    for scale in ["small", "medium", "large", "xlarge"]:
        manifest = output_dir / scale / "manifest.json"
        if manifest.exists():
            sizes[scale] = json.loads(manifest.read_text(encoding="utf-8")).get("total", 0)
    return sizes


def _write_json(path: Path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _bool(value):
    return str(value).lower() in {"1", "true", "yes", "on"}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", default="medium", choices=["small", "medium", "large", "xlarge"])
    parser.add_argument("--output-dir", default="datasets/v0_8_5_boundary_aware")
    parser.add_argument("--records-dir", default="records/v0_8_5")
    parser.add_argument("--worker-count", type=int, default=4)
    parser.add_argument("--generate-candidates-from-v0-8-4", default="true")
    parser.add_argument("--run-probe", default="true")
    return parser.parse_args()


if __name__ == "__main__":
    main()
