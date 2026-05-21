import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jianmu.self_learning.darwinforge.canonicalizer_reason_replay import replay_canonicalizer_reason
from jianmu.self_learning.darwinforge.ood_boundary_classifier import classify_ood_boundary_samples, summarize_boundary_records
from jianmu.self_learning.darwinforge.ood_candidate_datasets import candidate_counts, write_ood_candidate_datasets
from jianmu.self_learning.darwinforge.ood_slice_replay import load_v081_ood_slice
from jianmu.self_learning.darwinforge.supported_boundary_spec import default_supported_boundary_spec


def main():
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    replay = load_v081_ood_slice(REPO_ROOT, args.source_branch)
    current = _load_current_ood_records(Path(args.current_records_dir))
    spec = default_supported_boundary_spec()
    canonicalizer_replay = replay_canonicalizer_reason(replay["records"], spec)
    replay_boundary = classify_ood_boundary_samples(replay["records"], spec)
    current_boundary = classify_ood_boundary_samples(current, spec)
    combined_records = replay_boundary["records"] + current_boundary["records"]
    combined_boundary = {"records": combined_records, **summarize_boundary_records(combined_records)}
    dataset_manifest = {}
    if _bool(args.generate_candidate_datasets):
        dataset_manifest = write_ood_candidate_datasets(combined_records, REPO_ROOT / "datasets" / "v0_8_4_ood_boundary_candidates")
    metrics = {
        "source_branch": args.source_branch,
        "source_record_paths": replay["source_record_paths"],
        "replay_sample_count": replay["replay_sample_count"],
        "partial_replay": replay["partial_replay"],
        "missing_field_counts": replay["missing_field_counts"],
        "current_sample_count": len(current),
        "canonicalizer_reason_replay": {k: v for k, v in canonicalizer_replay.items() if k != "records"},
        "ood_boundary_classification": {k: v for k, v in combined_boundary.items() if k not in {"records", "examples_by_boundary_label"}},
        "candidate_dataset_manifest": dataset_manifest,
        **candidate_counts(combined_records),
        "real_promotion_enabled": False,
    }
    paths = write_outputs(output_dir, metrics, replay, canonicalizer_replay, combined_boundary, spec, dataset_manifest)
    print(json.dumps({"metrics": paths["metrics"], "report": paths["report"], "replay_sample_count": metrics["replay_sample_count"]}, ensure_ascii=False, indent=2))


def write_outputs(output_dir: Path, metrics, replay, canonicalizer_replay, boundary, spec, dataset_manifest):
    paths = {
        "metrics": output_dir / "ood_slice_replay_metrics.json",
        "report": output_dir / "ood_slice_replay_report.md",
        "replay_samples": output_dir / "replay_samples.jsonl",
        "canonicalizer_reason": output_dir / "canonicalizer_reason_replay.json",
        "canonicalizer_examples": output_dir / "canonicalizer_reason_examples.jsonl",
        "boundary": output_dir / "ood_boundary_classification.json",
        "boundary_examples": output_dir / "ood_boundary_examples.jsonl",
        "spec": output_dir / "supported_boundary_spec.json",
        "candidate_manifest": output_dir / "candidate_dataset_manifest.json",
        "mainline_md": output_dir / "mainline_conclusion.md",
        "mainline_json": output_dir / "mainline_conclusion.json",
    }
    _write_json(paths["metrics"], metrics)
    paths["report"].write_text(_report(metrics), encoding="utf-8")
    paths["replay_samples"].write_text(_jsonl(replay["records"]), encoding="utf-8")
    _write_json(paths["canonicalizer_reason"], {k: v for k, v in canonicalizer_replay.items() if k != "records"})
    paths["canonicalizer_examples"].write_text(_jsonl(canonicalizer_replay["records"][:200]), encoding="utf-8")
    _write_json(paths["boundary"], {k: v for k, v in boundary.items() if k not in {"records", "examples_by_boundary_label"}})
    paths["boundary_examples"].write_text(_jsonl(_flatten_examples(boundary.get("examples_by_boundary_label", {}))), encoding="utf-8")
    _write_json(paths["spec"], spec.to_dict())
    _write_json(paths["candidate_manifest"], dataset_manifest)
    mainline = _mainline(metrics)
    paths["mainline_md"].write_text(mainline["markdown"], encoding="utf-8")
    _write_json(paths["mainline_json"], mainline["json"])
    return {k: str(v) for k, v in paths.items()}


def _report(metrics):
    can = metrics["canonicalizer_reason_replay"]
    boundary = metrics["ood_boundary_classification"]
    lines = [
        "# OOD Slice Replay & Generalization Boundary（分布外切片回放与泛化边界）",
        "",
        "## Source Slice Loading（源切片加载）",
        f"- source_branch（源分支）: {metrics['source_branch']}",
        f"- source_record_paths（源记录路径）: {metrics['source_record_paths']}",
        f"- replay_sample_count（回放样本数）: {metrics['replay_sample_count']}",
        f"- partial_replay（部分回放）: {metrics['partial_replay']}",
        f"- missing_field_counts（缺失字段计数）: {metrics['missing_field_counts']}",
        "",
        "## Supported Boundary Spec（支持边界规格）",
        "- Current supported boundary remains bounded arithmetic / TargetIR routing. English arithmetic stays future-domain by default.",
        "",
        "## Canonicalizer Reason Replay（规范化原因回放）",
        f"- old_canonicalizer_reason_count（旧规范化原因计数）: {can['old_canonicalizer_reason_count']}",
        f"- new_canonicalizer_reason_count（新规范化原因计数）: {can['new_canonicalizer_reason_count']}",
        f"- canonicalizer_reason_confirmed（规范化原因确认）: {can['canonicalizer_reason_confirmed']}",
        f"- reason_not_reproduced（未复现原因）: {can['reason_not_reproduced']}",
        "",
        "## OOD Boundary Classification（分布外边界分类）",
        f"- ood_boundary_distribution（分布外边界分布）: {boundary['ood_boundary_distribution']}",
        "",
        "## Candidate Datasets（候选数据集）",
        f"- supported_expansion_candidates（支持域扩展候选）: {metrics['supported_expansion_candidates_count']}",
        f"- future_domain_candidates（未来能力候选）: {metrics['future_domain_candidates_count']}",
        f"- true_false_accept_cases（真正误接收案例）: {metrics['true_false_accept_cases_count']}",
        f"- label_review_cases（标签复审案例）: {metrics['label_review_cases_count']}",
        "",
        "## Paper Relevance（论文相关性）",
        "- This records the boundary audit needed before treating near-OOD samples as supported expansion candidates.",
        "",
        "## Updated Mainline Judgment（更新主线判断）",
        "- OOD accepted samples remain mixed. Candidate datasets are audit outputs only, not training-label changes.",
        "",
        "## Non-Claims（非主张）",
        "- This does not prove stable convergence.",
        "- This does not prove general program synthesis.",
        "- This does not prove solved arithmetic, AGI, Transformer replacement, advantage over same-size LLM, safe real promotion, or automatic near-OOD success.",
    ]
    return "\n".join(lines) + "\n"


def _mainline(metrics):
    can = metrics["canonicalizer_reason_replay"]
    boundary = metrics["ood_boundary_classification"]
    data = {
        "proved": [
            "v0.8.1 OOD guard-stress slice was loaded for replay where source records were available",
            "boundary labels and candidate datasets were generated without changing training labels",
        ],
        "not_proved": [
            "stable convergence",
            "general program synthesis",
            "near-OOD automatic supported success",
            "safe real promotion",
        ],
        "new_bottleneck": "supported boundary requires human review before expansion",
        "changes_mainline_judgment": False,
        "next_minimal_action": "review candidate datasets and rerun guard training only after boundary approval",
        "paper_relevance": ["OOD boundary table", "canonicalizer reason replay result"],
        "must_reproduce": ["exact source-slice replay if future records add missing fields", "manual review of supported expansion candidates"],
        "risk": {"pseudo_improvement": False, "negative_transfer": False, "ood_pollution": True},
        "canonicalizer_made_it_look_supported_reproduced": can["canonicalizer_reason_confirmed"],
        "ood_boundary_distribution": boundary["ood_boundary_distribution"],
        "supported_expansion_candidates_generated": metrics["supported_expansion_candidates_count"] > 0,
        "true_false_accept_guard_training_candidates_generated": metrics["true_false_accept_cases_count"] > 0,
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
        "## 是否改变主线判断",
        f"- {data['changes_mainline_judgment']}",
        "",
        "## 下一版最小必要动作",
        f"- {data['next_minimal_action']}",
        "",
        "## 哪些结果可以进入 paper draft",
        *[f"- {item}" for item in data["paper_relevance"]],
        "",
        "## 哪些结果必须复验",
        *[f"- {item}" for item in data["must_reproduce"]],
        "",
        "## canonicalizer_made_it_look_supported 是否复现",
        f"- {data['canonicalizer_made_it_look_supported_reproduced']}",
        "",
        "## OOD accepted 分类",
        f"- {data['ood_boundary_distribution']}",
    ]
    return {"markdown": "\n".join(md) + "\n", "json": data}


def _load_current_ood_records(records_dir: Path):
    path = records_dir / "ood_precision_examples.jsonl"
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rows.append(
            {
                "source_version": "v0.8.3",
                "sample_id": row.get("sample_id"),
                "raw_text": row.get("raw_text"),
                "canonical_text": row.get("canonical_text"),
                "ood_class": row.get("ood_class"),
                "accepted_as_supported": row.get("accepted_as_supported", True),
                "false_accept_reason": row.get("false_accept_reason"),
            }
        )
    return rows


def _flatten_examples(examples):
    rows = []
    for label, items in examples.items():
        for item in items:
            row = dict(item)
            row["example_label"] = label
            rows.append(row)
    return rows


def _jsonl(rows):
    return "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)


def _write_json(path: Path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _bool(value):
    return str(value).lower() in {"1", "true", "yes", "on"}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_7_0")
    parser.add_argument("--source-branch", default="v0.8.1-ood-toxicity-longrun-scale")
    parser.add_argument("--current-records-dir", default="records/v0_8_3")
    parser.add_argument("--output-dir", default="records/v0_8_4")
    parser.add_argument("--generate-candidate-datasets", default="true")
    return parser.parse_args()


if __name__ == "__main__":
    main()
