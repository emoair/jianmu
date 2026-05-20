import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jianmu.self_learning.darwinforge.capability_audit import audit_supported_sample_capability, run_path_forcing_smoke_test
from jianmu.self_learning.darwinforge.rootforge_growth_trainer import RootForgeGrowthConfig, RootForgeGrowthTrainer
from jianmu.self_learning.datasets.symbol_grounding import load_symbol_grounding_split
from jianmu.self_learning.preprocessing.symbol_canonicalizer import canonicalize_symbols


def main():
    args = parse_args()
    dataset_dir = Path(args.dataset_dir)
    if not (dataset_dir / "jianmu_v0_7_0_symbol_grounding_train.jsonl").exists():
        quick_dir = Path("datasets/v0_7_0_quick")
        subprocess.run([sys.executable, "-m", "jianmu.self_learning.datasets.symbol_grounding", "--size", "600", "--seed", "42", "--out", str(quick_dir)], check=True)
        dataset_dir = quick_dir
    config = RootForgeGrowthConfig.for_mode(
        args.mode,
        train_limit=args.train_limit,
        eval_limit=args.eval_limit,
        ood_limit=args.ood_limit,
        generations=args.generations,
        beam_size=args.beam_size,
        clone_count_per_layer=args.clone_count_per_layer,
        perturbation_scale=args.perturbation_scale,
        population_per_layer=args.population_per_layer,
        seed=args.seed,
    )
    if args.mode == "quick" and args.generations is None:
        config.generations = 4
    train = load_symbol_grounding_split(dataset_dir, "train")
    eval_samples = load_symbol_grounding_split(dataset_dir, "eval")
    ood = load_symbol_grounding_split(dataset_dir, "ood")
    selected_train = train[: config.train_limit]
    selected_eval = eval_samples[: config.eval_limit]
    selected_ood = ood[: config.ood_limit]
    supported_for_audit = selected_train + selected_eval
    path_forcing = run_path_forcing_smoke_test(supported_for_audit)
    root_metrics = RootForgeGrowthTrainer(selected_train, selected_eval, selected_ood, config).train()
    capability = audit_supported_sample_capability(supported_for_audit, beam_diagnostics=root_metrics.get("eval_diagnostics", []))
    pollution = _pollution_audit(supported_for_audit + selected_ood)
    metrics = _combine_metrics(config, dataset_dir, path_forcing, capability, root_metrics, pollution)
    paths = _write_outputs(metrics, path_forcing, capability, root_metrics, Path(args.records_dir))
    print(f"dataset dir: {dataset_dir}")
    print(f"mode: {config.mode}")
    print(f"train/eval/ood: {metrics['train_sample_count']} / {metrics['eval_sample_count']} / {metrics['ood_sample_count']}")
    for key in [
        "path_forcing_exact_match_rate",
        "path_forcing_literal_only_success_rate",
        "path_forcing_precedence_success_rate",
        "synthesizable_by_forced_path_rate",
        "router_candidate_failure_rate",
        "synthesis_capability_failure_rate",
        "dataset_capability_mismatch_count",
        "literal_only_targetir_exact_match",
        "precedence_div_add_success_rate",
        "target_ir_exact_match_top1",
        "target_ir_exact_match_beam_oracle",
        "correct_targetir_in_beam_rate",
        "candidate_space_failure_rate",
        "ranking_failure_rate",
        "train_low_score_correct_count",
        "eval_low_score_correct_count",
        "low_score_correct_without_action_count",
        "regrowth_queue_added_count",
        "stable_root_buffer_added_count",
        "necrosis_queue_added_count",
        "artifact_suffix_stripped_count",
        "ood_rejection_rate",
        "ood_false_accept_rate",
    ]:
        print(f"{key}: {metrics.get(key)}")
    print(f"metrics path: {paths['metrics_path']}")
    print(f"report path: {paths['report_path']}")
    print(f"path forcing path: {paths['path_forcing_path']}")
    print(f"capability audit path: {paths['capability_audit_path']}")
    print(f"viability path: {paths['viability_path']}")
    print(f"actions path: {paths['actions_path']}")


def _combine_metrics(config, dataset_dir, path_forcing, capability, root_metrics, pollution):
    keys = [
        "literal_only_targetir_exact_match",
        "precedence_div_add_success_rate",
        "target_ir_exact_match_top1",
        "target_ir_exact_match_beam_oracle",
        "correct_targetir_in_beam_rate",
        "candidate_space_failure_rate",
        "ranking_failure_rate",
        "train_low_score_correct_count",
        "eval_low_score_correct_count",
        "low_score_correct_without_action_count",
        "regrowth_queue_added_count",
        "stable_root_buffer_added_count",
        "necrosis_queue_added_count",
        "ood_rejection_rate",
        "ood_false_accept_rate",
        "first_wrong_layer_distribution",
    ]
    metrics = {key: root_metrics.get(key) for key in keys}
    metrics.update({key: path_forcing.get(key) for key in path_forcing if key != "rows"})
    metrics.update({key: capability.get(key) for key in capability if key != "rows"})
    metrics.update(pollution)
    metrics.update(
        {
            "config": config.to_dict(),
            "dataset_dir": str(dataset_dir),
            "mode": config.mode,
            "train_sample_count": root_metrics["train_sample_count"],
            "eval_sample_count": root_metrics["eval_sample_count"],
            "ood_sample_count": root_metrics["ood_sample_count"],
        }
    )
    return metrics


def _pollution_audit(samples):
    examples = []
    count = 0
    for sample in samples:
        result = canonicalize_symbols(sample["input_text"])
        if "stripped_dataset_artifact_suffix" in result.warnings:
            count += 1
            if len(examples) < 10:
                examples.append({"raw_text": sample["input_text"], "canonical_text": result.canonical_text, "warnings": result.warnings})
    return {"artifact_suffix_stripped_count": count, "artifact_suffix_examples": examples}


def _write_outputs(metrics, path_forcing, capability, root_metrics, records_dir: Path):
    records_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "metrics_path": records_dir / "capability_alignment_metrics.json",
        "report_path": records_dir / "capability_alignment_report.md",
        "path_forcing_path": records_dir / "path_forcing_smoke.jsonl",
        "capability_audit_path": records_dir / "capability_audit.jsonl",
        "curve_path": records_dir / "rootforge_alignment_curve.jsonl",
        "candidates_path": records_dir / "rootforge_alignment_candidates.jsonl",
        "viability_path": records_dir / "rootforge_alignment_viability.jsonl",
        "actions_path": records_dir / "rootforge_alignment_actions.jsonl",
        "failure_examples_path": records_dir / "rootforge_alignment_failure_examples.json",
    }
    paths["metrics_path"].write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    paths["report_path"].write_text(_report(metrics), encoding="utf-8")
    paths["path_forcing_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in path_forcing["rows"]), encoding="utf-8")
    paths["capability_audit_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in capability["rows"]), encoding="utf-8")
    paths["curve_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in root_metrics["curve"]), encoding="utf-8")
    paths["candidates_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in root_metrics["candidates"]), encoding="utf-8")
    paths["viability_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in root_metrics["viability"]), encoding="utf-8")
    action_rows = []
    for key in ["regrowth_events", "necrosis_events"]:
        for row in root_metrics.get(key, []):
            action_rows.append({"action_source": key, **row})
    paths["actions_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in action_rows), encoding="utf-8")
    paths["failure_examples_path"].write_text(json.dumps(root_metrics["failure_examples"], ensure_ascii=False, indent=2), encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


def _report(metrics):
    return "\n".join(
        [
            "# RootForge Capability Alignment（根铸能力对齐） Report",
            "",
            "## Candidate Space Repair（候选空间修复）",
            "- Branch Prior Repair（分支先验修复） covers Literal-Only TargetIR（单字面量目标中间表示）, Literal Value Policy（字面量值策略）, target_builder literal routing（字面量目标构造路由）, and negative-number routing（负数路由）.",
            "",
            "## Path-Forcing Smoke Test（强制路径冒烟测试）",
            f"- path_forcing_exact_match_rate（强制路径精确匹配率）: {metrics.get('path_forcing_exact_match_rate', 0.0)}",
            f"- path_forcing_literal_only_success_rate（单字面量强制成功率）: {metrics.get('path_forcing_literal_only_success_rate', 0.0)}",
            f"- path_forcing_precedence_success_rate（优先级强制成功率）: {metrics.get('path_forcing_precedence_success_rate', 0.0)}",
            "",
            "## Capability Audit（能力审计）",
            f"- synthesizable_by_forced_path_rate（强制路径可合成率）: {metrics.get('synthesizable_by_forced_path_rate', 0.0)}",
            f"- router_candidate_failure_rate（路由候选失败率）: {metrics.get('router_candidate_failure_rate', 0.0)}",
            f"- synthesis_capability_failure_rate（合成能力失败率）: {metrics.get('synthesis_capability_failure_rate', 0.0)}",
            f"- dataset_capability_mismatch_count（数据能力不匹配数量）: {metrics.get('dataset_capability_mismatch_count', 0)}",
            "",
            "## Beam Result（束搜索结果）",
            f"- target_ir_exact_match_top1（Top1 目标中间表示精确匹配）: {metrics.get('target_ir_exact_match_top1', 0.0)}",
            f"- target_ir_exact_match_beam_oracle（束内上限）: {metrics.get('target_ir_exact_match_beam_oracle', 0.0)}",
            f"- correct_targetir_in_beam_rate（正确目标中间表示在束内率）: {metrics.get('correct_targetir_in_beam_rate', 0.0)}",
            f"- candidate_space_failure_rate（候选空间失败率）: {metrics.get('candidate_space_failure_rate', 0.0)}",
            f"- ranking_failure_rate（排序失败率）: {metrics.get('ranking_failure_rate', 0.0)}",
            "",
            "## Root Viability（根系可生性）",
            f"- train_low_score_correct_count（训练集低分正确根数量）: {metrics.get('train_low_score_correct_count', 0)}",
            f"- eval_low_score_correct_count（评测集低分正确根数量）: {metrics.get('eval_low_score_correct_count', 0)}",
            f"- low_score_correct_without_action_count（低分正确根无动作数量）: {metrics.get('low_score_correct_without_action_count', 0)}",
            "",
            "## Regrowth Action（再生动作）",
            f"- regrowth_queue_added_count（再生队列加入数量）: {metrics.get('regrowth_queue_added_count', 0)}",
            f"- stable_root_buffer_added_count（稳定根缓冲加入数量）: {metrics.get('stable_root_buffer_added_count', 0)}",
            f"- necrosis_queue_added_count（坏死队列加入数量）: {metrics.get('necrosis_queue_added_count', 0)}",
            "",
            "## Data Pollution Audit（数据污染审计）",
            f"- artifact_suffix_stripped_count（伪影后缀剥离数量）: {metrics.get('artifact_suffix_stripped_count', 0)}",
            f"- artifact_suffix_examples（伪影后缀示例）: {metrics.get('artifact_suffix_examples', [])[:3]}",
            "",
            "## Non-Claims（非主张）",
            "- This does not prove stable DarwinForge（达尔文进化炉） convergence.",
            "- This does not prove general program synthesis.",
            "- This does not train C source text.",
            "- This does not patch old source code.",
            "- This is RootForge Capability Alignment（根铸能力对齐）, not a release claim.",
        ]
    ) + "\n"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_7_0")
    parser.add_argument("--mode", choices=["quick", "medium"], default="quick")
    parser.add_argument("--train-limit", type=int, default=None)
    parser.add_argument("--eval-limit", type=int, default=None)
    parser.add_argument("--ood-limit", type=int, default=None)
    parser.add_argument("--generations", type=int, default=None)
    parser.add_argument("--beam-size", type=int, default=None)
    parser.add_argument("--clone-count-per-layer", type=int, default=None)
    parser.add_argument("--perturbation-scale", type=float, default=None)
    parser.add_argument("--population-per-layer", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--records-dir", default="records/v0_7_5")
    return parser.parse_args()


if __name__ == "__main__":
    main()
