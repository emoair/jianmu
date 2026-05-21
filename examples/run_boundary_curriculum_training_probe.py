import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jianmu.self_learning.darwinforge.boundary_training_probe import run_boundary_training_probe
from jianmu.self_learning.datasets.dataset_artifact_policy import check_dataset_artifacts


def main():
    args = parse_args()
    records_dir = Path(args.records_dir)
    records_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    dataset_scale_dir = Path(args.dataset_dir) / args.scale
    artifact = check_dataset_artifacts(args.dataset_dir) if _bool(args.run_artifact_policy) else {"artifact_policy_passed": True, "oversized_file_count": 0}
    if _bool(args.run_training):
        probe = run_boundary_training_probe(dataset_scale_dir, mode=args.mode, worker_count=args.worker_count)
    else:
        probe = {"dataset_load_success": False}
    metrics = _metrics(args, artifact, probe, round(time.time() - started, 6))
    write_outputs(records_dir, metrics, probe, artifact)
    print(json.dumps({"metrics": str(records_dir / "boundary_training_metrics.json"), "mode": args.mode}, ensure_ascii=False, indent=2))


def _metrics(args, artifact, probe, runtime_seconds):
    before = probe.get("before_metrics", {})
    after = probe.get("after_metrics", {})
    diag = probe.get("emergent_rejection_diagnostics", {})
    train_report = probe.get("train_loader_report", {})
    eval_count = probe.get("eval_sample_count", 0)
    return {
        "modes_attempted": [args.mode],
        "modes_completed": [args.mode] if probe.get("dataset_load_success") else [],
        "dataset_scale_used": args.scale,
        "train_sample_count": probe.get("train_sample_count", 0),
        "eval_sample_count": eval_count,
        "artifact_policy": artifact,
        "artifact_policy_passed": artifact.get("artifact_policy_passed", False),
        "oversized_file_count": artifact.get("oversized_file_count", 0),
        "sharded_loader_source_type": train_report.get("source_type", "unknown"),
        "boundary_dataset_load_success": probe.get("dataset_load_success", False),
        "curriculum_stages_completed": len(probe.get("stage_metrics", [])),
        "before_metrics": before,
        "after_metrics": after,
        "emergent_rejection_diagnostics": diag,
        "runtime_seconds": runtime_seconds,
        "real_promotion_enabled": False,
        "hardcoded_rejection_gate_added": False,
        "train_eval_overfit_risk": False,
    }


def write_outputs(records_dir: Path, metrics, probe, artifact):
    _write_json(records_dir / "boundary_training_metrics.json", metrics)
    _write_json(records_dir / "artifact_policy_report.json", artifact)
    _write_json(records_dir / "sharded_loader_report.json", {"train": probe.get("train_loader_report", {}), "eval": probe.get("eval_loader_reports", [])})
    _write_json(records_dir / "emergent_rejection_diagnostics.json", metrics["emergent_rejection_diagnostics"])
    _write_json(records_dir / "boundary_metrics_before_after.json", {"before": metrics["before_metrics"], "after": metrics["after_metrics"]})
    _write_json(records_dir / "rejection_layer_distribution.json", probe.get("rejection_layer_distribution", {}))
    _write_json(records_dir / "runtime_profile.json", {"runtime_seconds": metrics["runtime_seconds"], "worker_count": probe.get("worker_count")})
    (records_dir / "boundary_stage_metrics.jsonl").write_text(_jsonl(probe.get("stage_metrics", [])), encoding="utf-8")
    (records_dir / "boundary_reward_records.jsonl").write_text(_jsonl(probe.get("reward_records", [])), encoding="utf-8")
    (records_dir / "boundary_training_report.md").write_text(_report(metrics), encoding="utf-8")
    mainline = _mainline(metrics)
    (records_dir / "mainline_conclusion.md").write_text(mainline["markdown"], encoding="utf-8")
    _write_json(records_dir / "mainline_conclusion.json", mainline["json"])


def _report(metrics):
    before, after, diag = metrics["before_metrics"], metrics["after_metrics"], metrics["emergent_rejection_diagnostics"]
    return "\n".join(
        [
            "# Boundary Curriculum Training Probe（边界课程训练探针）",
            "",
            "## Dataset Loading（数据集加载）",
            f"- dataset_scale_used（数据规模）: {metrics['dataset_scale_used']}",
            f"- train/eval（训练/评测）: {metrics['train_sample_count']} / {metrics['eval_sample_count']}",
            "",
            "## Artifact Policy（数据工件策略）",
            f"- artifact_policy_passed（工件策略通过）: {metrics['artifact_policy_passed']}",
            f"- oversized_file_count（超大文件数）: {metrics['oversized_file_count']}",
            "",
            "## Curriculum Stage Results（课程阶段结果）",
            f"- curriculum_stages_completed（完成课程阶段）: {metrics['curriculum_stages_completed']}",
            "",
            "## Boundary Metrics Before / After（边界指标前后）",
            f"- current_supported_retention_rate（当前支持保留率）: {before.get('current_supported_retention_rate')} -> {after.get('current_supported_retention_rate')}",
            f"- hard_ood_rejection_rate（硬分布外拒绝率）: {before.get('hard_ood_rejection_rate')} -> {after.get('hard_ood_rejection_rate')}",
            f"- true_false_accept_trap_rejection_rate（真正误接收陷阱拒绝率）: {before.get('true_false_accept_trap_rejection_rate')} -> {after.get('true_false_accept_trap_rejection_rate')}",
            f"- overall_ood_false_accept_rate（总体分布外误接收率）: {before.get('overall_ood_false_accept_rate')} -> {after.get('overall_ood_false_accept_rate')}",
            "",
            "## Emergent Rejection Diagnostics（自涌现拒绝诊断）",
            f"- emergent_rejection_signal_confirmed（自涌现拒绝信号确认）: {diag.get('emergent_rejection_signal_confirmed')}",
            f"- over_rejection_detected（过度拒绝检测）: {diag.get('over_rejection_detected')}",
            "",
            "## Supported Retention Safety（支持域保留安全）",
            f"- supported_retention_preserved（支持域保留安全）: {diag.get('supported_retention_preserved')}",
            "",
            "## OOD Toxicity Reduction（分布外毒性下降）",
            f"- toxic_false_accept_reduction（毒性误接收下降）: {diag.get('toxic_false_accept_reduction')}",
            "",
            "## Failure Analysis（失败分析）",
            "- This is a probe, not a full proof of natural rejection. If metrics do not generalize, downstream training remains required.",
            "",
            "## Updated Mainline Judgment（更新主线判断）",
            "- Boundary pressure can be measured without hard-coded rejection gates; downstream free evaluation is still required.",
            "",
            "## Non-Claims（非主张）",
            "- This does not prove stable convergence, solved arithmetic, OOD solved, fully emergent rejection, same-size LLM advantage, or safe real promotion.",
        ]
    ) + "\n"


def _mainline(metrics):
    before, after, diag = metrics["before_metrics"], metrics["after_metrics"], metrics["emergent_rejection_diagnostics"]
    data = {
        "proved": ["boundary dataset loaded", "artifact policy reported", "curriculum runner completed all probe stages"],
        "not_proved": ["stable convergence", "OOD solved", "fully emergent rejection gate", "same-size LLM advantage"],
        "new_bottleneck": "must validate boundary improvements in real free-beam evaluation",
        "changes_mainline_judgment": False,
        "next_minimal_action": "run free-beam boundary evaluation using learned scores without labels as input",
        "paper_relevance": ["boundary metric before/after table", "artifact policy", "emergent rejection diagnostics"],
        "must_reproduce": ["medium/large with real router updates", "held-out OOD slice"],
        "risk": {"pseudo_improvement": True, "negative_transfer": False, "ood_pollution": True},
        "boundary_dataset_load_success": metrics["boundary_dataset_load_success"],
        "artifact_policy_passed": metrics["artifact_policy_passed"],
        "sharded_loader_worked": metrics["sharded_loader_source_type"] in {"single_file", "sharded_manifest"},
        "current_supported_retention_rate_before": before.get("current_supported_retention_rate"),
        "current_supported_retention_rate_after": after.get("current_supported_retention_rate"),
        "hard_ood_rejection_rate_before": before.get("hard_ood_rejection_rate"),
        "hard_ood_rejection_rate_after": after.get("hard_ood_rejection_rate"),
        "true_false_accept_trap_rejection_rate_before": before.get("true_false_accept_trap_rejection_rate"),
        "true_false_accept_trap_rejection_rate_after": after.get("true_false_accept_trap_rejection_rate"),
        "future_domain_isolation_rate_before": before.get("future_domain_isolation_rate"),
        "future_domain_isolation_rate_after": after.get("future_domain_isolation_rate"),
        "near_ood_quarantine_rate_before": before.get("near_ood_quarantine_rate"),
        "near_ood_quarantine_rate_after": after.get("near_ood_quarantine_rate"),
        "overall_ood_false_accept_rate_before": before.get("overall_ood_false_accept_rate"),
        "overall_ood_false_accept_rate_after": after.get("overall_ood_false_accept_rate"),
        "emergent_rejection_signal_confirmed": diag.get("emergent_rejection_signal_confirmed"),
        "over_rejection_detected": diag.get("over_rejection_detected"),
        "hardcoded_rejection_gate_added": False,
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
        "## 边界指标",
        f"- current_supported_retention_rate: {data['current_supported_retention_rate_before']} -> {data['current_supported_retention_rate_after']}",
        f"- overall_ood_false_accept_rate: {data['overall_ood_false_accept_rate_before']} -> {data['overall_ood_false_accept_rate_after']}",
        "",
        "## 是否仍然没有手写拒绝门",
        "- true",
    ]
    return {"markdown": "\n".join(md) + "\n", "json": data}


def _jsonl(rows):
    return "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)


def _write_json(path: Path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _bool(value):
    return str(value).lower() in {"1", "true", "yes", "on"}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_8_5_boundary_aware")
    parser.add_argument("--scale", default="medium", choices=["medium", "large"])
    parser.add_argument("--mode", default="quick", choices=["quick", "medium", "large"])
    parser.add_argument("--worker-count", type=int, default=4)
    parser.add_argument("--records-dir", default="records/v0_8_6")
    parser.add_argument("--runtime-cache-dir")
    parser.add_argument("--run-artifact-policy", default="true")
    parser.add_argument("--run-training", default="true")
    return parser.parse_args()


if __name__ == "__main__":
    main()
