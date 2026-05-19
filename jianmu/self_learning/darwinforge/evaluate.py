import json
from pathlib import Path

from jianmu.self_learning.branchchain.toy_dataset import (
    build_architecture_aligned_toy_dataset,
    build_branchchain_toy_dataset,
    dataset_summary,
)
from jianmu.self_learning.branchchain.surface_features import extract_surface_features
from jianmu.self_learning.darwinforge.evolution import (
    CurriculumDarwinForgeTrainer,
    DarwinForgeTrainer,
    HindsightReRankingDarwinForgeTrainer,
    ParaphraseInvariantDarwinForgeTrainer,
)
from jianmu.self_learning.darwinforge.fitness import compute_fitness


RECORD_DIR = Path("records/v0_6")
METRICS_PATH = RECORD_DIR / "darwinforge_toy_metrics.json"
REPORT_PATH = RECORD_DIR / "darwinforge_toy_report.md"
CANDIDATES_PATH = RECORD_DIR / "darwinforge_toy_candidates.jsonl"
HARD_CASES_PATH = RECORD_DIR / "darwinforge_hard_cases.jsonl"

CURRICULUM_DIR = Path("records/v0_6_1")
CURRICULUM_METRICS_PATH = CURRICULUM_DIR / "curriculum_freezing_metrics.json"
CURRICULUM_REPORT_PATH = CURRICULUM_DIR / "curriculum_freezing_report.md"
CURRICULUM_CANDIDATES_PATH = CURRICULUM_DIR / "curriculum_freezing_candidates.jsonl"

THRESHOLD_DIR = Path("records/v0_6_2")
THRESHOLD_METRICS_PATH = THRESHOLD_DIR / "highest_stable_threshold_metrics.json"
THRESHOLD_REPORT_PATH = THRESHOLD_DIR / "highest_stable_threshold_report.md"
THRESHOLD_CANDIDATES_PATH = THRESHOLD_DIR / "highest_stable_threshold_candidates.jsonl"

GATED_DIR = Path("records/v0_6_3")
GATED_METRICS_PATH = GATED_DIR / "confidence_gated_metrics.json"
GATED_REPORT_PATH = GATED_DIR / "confidence_gated_report.md"
GATED_CANDIDATES_PATH = GATED_DIR / "confidence_gated_candidates.jsonl"

ARCH_ALIGNED_DIR = Path("records/v0_6_4")
ARCH_ALIGNED_METRICS_PATH = ARCH_ALIGNED_DIR / "architecture_aligned_dataset_metrics.json"
ARCH_ALIGNED_REPORT_PATH = ARCH_ALIGNED_DIR / "architecture_aligned_dataset_report.md"
ARCH_ALIGNED_CANDIDATES_PATH = ARCH_ALIGNED_DIR / "architecture_aligned_dataset_candidates.jsonl"

PARAPHRASE_DIR = Path("records/v0_6_5")
PARAPHRASE_METRICS_PATH = PARAPHRASE_DIR / "paraphrase_invariant_metrics.json"
PARAPHRASE_REPORT_PATH = PARAPHRASE_DIR / "paraphrase_invariant_report.md"
PARAPHRASE_CANDIDATES_PATH = PARAPHRASE_DIR / "paraphrase_invariant_candidates.jsonl"

RERANK_DIR = Path("records/v0_6_6")
RERANK_METRICS_PATH = RERANK_DIR / "hindsight_reranking_metrics.json"
RERANK_REPORT_PATH = RERANK_DIR / "hindsight_reranking_report.md"
RERANK_CANDIDATES_PATH = RERANK_DIR / "hindsight_reranking_candidates.jsonl"
RERANK_PRUNING_PATH = RERANK_DIR / "pruning_candidates.jsonl"


def run_darwinforge_toy(
    population_per_layer: int = 16,
    generations: int = 30,
    top_k_candidates: int = 3,
    seed: int = 42,
    compile_checks_per_generation: int = 8,
):
    RECORD_DIR.mkdir(parents=True, exist_ok=True)
    trainer = DarwinForgeTrainer(
        population_per_layer=population_per_layer,
        generations=generations,
        top_k_candidates=top_k_candidates,
        seed=seed,
        compile_checks_per_generation=compile_checks_per_generation,
    )
    report = trainer.train()
    metrics = report.to_dict()
    METRICS_PATH.write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    REPORT_PATH.write_text(_report_markdown(metrics), encoding="utf-8")
    trainer.hard_cases.save_jsonl(HARD_CASES_PATH)
    # Candidate archive keeps hard-case candidate summaries to avoid huge toy logs.
    CANDIDATES_PATH.write_text(
        "".join(json.dumps(item.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for item in trainer.hard_cases.items),
        encoding="utf-8",
    )
    metrics["report_path"] = str(REPORT_PATH)
    metrics["candidates_path"] = str(CANDIDATES_PATH)
    return metrics


def _report_markdown(metrics):
    first = metrics["metrics_by_generation"][0]
    final = metrics["metrics_by_generation"][-1]
    lines = [
        "# v0.6 DarwinForge Toy Report",
        "",
        "This is a minimal DarwinForge scaffold, not a completed system.",
        "",
        "## Summary",
        "",
        f"- dataset size: {metrics['dataset_size']}",
        f"- population_per_layer: {metrics['population_per_layer']}",
        f"- generations: {metrics['generations']}",
        f"- top_k_candidates: {metrics['top_k_candidates']}",
        f"- compile_checks_per_generation: {metrics['compile_checks_per_generation']}",
        f"- generation 0 mean_fitness: {first['mean_fitness']}",
        f"- final mean_fitness: {final['mean_fitness']}",
        f"- generation 0 target_ir_exact_match_rate: {first['target_ir_exact_match_rate']}",
        f"- final target_ir_exact_match_rate: {final['target_ir_exact_match_rate']}",
        f"- generation 0 missing_layer_rate: {first['missing_layer_rate']}",
        f"- final missing_layer_rate: {final['missing_layer_rate']}",
        f"- hard_case_count: {metrics['hard_case_count']}",
        "",
        "## Fitness Curves",
        "",
        "- mean_fitness: " + ", ".join(str(row["mean_fitness"]) for row in metrics["metrics_by_generation"]),
        "- target_ir_exact_match_rate: " + ", ".join(str(row["target_ir_exact_match_rate"]) for row in metrics["metrics_by_generation"]),
        "- missing_layer_rate: " + ", ".join(str(row["missing_layer_rate"]) for row in metrics["metrics_by_generation"]),
        "",
        "## Most Common Final Wrong Branch Decisions",
        "",
    ]
    for label, count in final["most_common_wrong_branch_decisions"]:
        lines.append(f"- {label}: {count}")
    lines.extend(
        [
            "",
            "## Non-Claims",
            "",
            "- This does not prove AGI.",
            "- This does not prove Transformer replacement.",
            "- This does not prove hardware BPU implementation.",
            "- This does not prove general program synthesis.",
            "- This does not train C source text.",
            "- This is a minimal DarwinForge scaffold.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_curriculum_freezing_toy(
    population_per_layer: int = 16,
    generations: int = 40,
    top_k_candidates: int = 3,
    seed: int = 42,
    compile_checks_per_generation: int = 4,
):
    CURRICULUM_DIR.mkdir(parents=True, exist_ok=True)
    trainer = CurriculumDarwinForgeTrainer(
        population_per_layer=population_per_layer,
        generations=generations,
        top_k_candidates=top_k_candidates,
        seed=seed,
        compile_checks_per_generation=compile_checks_per_generation,
    )
    metrics = trainer.train()
    candidate_records = metrics.pop("candidate_records")
    CURRICULUM_METRICS_PATH.write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    CURRICULUM_REPORT_PATH.write_text(_curriculum_report_markdown(metrics), encoding="utf-8")
    CURRICULUM_CANDIDATES_PATH.write_text(
        "".join(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for record in candidate_records[-200:]),
        encoding="utf-8",
    )
    metrics["report_path"] = str(CURRICULUM_REPORT_PATH)
    metrics["candidates_path"] = str(CURRICULUM_CANDIDATES_PATH)
    return metrics


def _curriculum_report_markdown(metrics):
    first = metrics["metrics_by_generation"][0]
    final = metrics["metrics_by_generation"][-1]
    best = metrics["hall_of_fame"]["best_metrics"]
    lines = [
        "# v0.6.1 BranchChain Curriculum Freezing Report",
        "",
        "This is a training-dynamics scaffold, not a stable convergence claim.",
        "",
        "## Final vs Best",
        "",
        f"- generation 0 mean_fitness: {first['mean_fitness']}",
        f"- final mean_fitness: {final['mean_fitness']}",
        f"- best mean_fitness: {best.get('mean_fitness')}",
        f"- generation 0 target_ir_exact_match_rate: {first['target_ir_exact_match_rate']}",
        f"- final target_ir_exact_match_rate: {final['target_ir_exact_match_rate']}",
        f"- best target_ir_exact_match_rate: {best.get('target_ir_exact_match_rate')}",
        f"- generation 0 missing_layer_rate: {first['missing_layer_rate']}",
        f"- final missing_layer_rate: {final['missing_layer_rate']}",
        f"- best_generation: {metrics['hall_of_fame']['best_generation']}",
        "",
        "## Freeze Events",
        "",
    ]
    for event in metrics["curriculum"]["freeze_events"]:
        lines.append(f"- generation {event['generation']}: {event['layer']} ({event['reason']})")
    if not metrics["curriculum"]["freeze_events"]:
        lines.append("- none")
    lines.extend(["", "## Unfreeze Events", ""])
    for event in metrics["curriculum"]["unfreeze_events"]:
        lines.append(f"- generation {event['generation']}: {event['layer']} ({event['reason']})")
    if not metrics["curriculum"]["unfreeze_events"]:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Curves",
            "",
            "- active_layer: " + ", ".join(row["active_layer"] for row in metrics["metrics_by_generation"]),
            "- mean_fitness: " + ", ".join(str(row["mean_fitness"]) for row in metrics["metrics_by_generation"]),
            "- target_ir_exact_match_rate: " + ", ".join(str(row["target_ir_exact_match_rate"]) for row in metrics["metrics_by_generation"]),
            "- missing_layer_rate: " + ", ".join(str(row["missing_layer_rate"]) for row in metrics["metrics_by_generation"]),
            "",
            "## Hard-Case Attribution Summary",
            "",
        ]
    )
    for layer, payload in sorted(final.get("hard_case_attribution", {}).items()):
        lines.append(f"- {layer}: error_rate={payload['error_rate']}, severity={payload['severity']}")
    lines.extend(
        [
            "",
            "## Non-Claims",
            "",
            "- This does not prove stable DarwinForge convergence.",
            "- This does not prove general program synthesis.",
            "- This does not train C source text.",
            "- This does not patch old source code.",
            "- This does not prove AGI, Transformer replacement, or hardware BPU implementation.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_highest_stable_threshold_search_toy(
    population_per_layer: int = 16,
    generations: int = 60,
    top_k_candidates: int = 3,
    seed: int = 42,
    compile_checks_per_generation: int = 0,
):
    THRESHOLD_DIR.mkdir(parents=True, exist_ok=True)
    trainer = CurriculumDarwinForgeTrainer(
        population_per_layer=population_per_layer,
        generations=generations,
        top_k_candidates=top_k_candidates,
        seed=seed,
        compile_checks_per_generation=compile_checks_per_generation,
    )
    metrics = trainer.train()
    candidate_records = metrics.pop("candidate_records")
    THRESHOLD_METRICS_PATH.write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    THRESHOLD_REPORT_PATH.write_text(_threshold_report_markdown(metrics), encoding="utf-8")
    THRESHOLD_CANDIDATES_PATH.write_text(
        "".join(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for record in candidate_records[-200:]),
        encoding="utf-8",
    )
    metrics["report_path"] = str(THRESHOLD_REPORT_PATH)
    metrics["candidates_path"] = str(THRESHOLD_CANDIDATES_PATH)
    return metrics


def _threshold_report_markdown(metrics):
    first = metrics["metrics_by_generation"][0]
    final = metrics["metrics_by_generation"][-1]
    best = metrics["hall_of_fame"]["best_metrics"]
    curriculum = metrics["curriculum"]
    threshold = curriculum["threshold_controller"]
    support_state = threshold["states"].get("support_gate", {})
    selection_notes = []
    for layer, recall in final.get("per_layer_recall_at_k", {}).items():
        winner = final.get("per_layer_winner_accuracy", {}).get(layer, 0.0)
        if recall > winner:
            selection_notes.append(f"- {layer}: layer_recall@k（层级候选召回）={recall} > winner_accuracy（赢家准确率）={winner}")
    lines = [
        "# v0.6.2 Highest-Stable Threshold Search（最高稳定阈值搜索） Report",
        "",
        "This is a threshold-search scaffold for BranchChain（分支链） curriculum training.",
        "",
        "## Final vs Best（最终与历史最佳）",
        "",
        f"- generation 0 mean_fitness（平均适应度）: {first['mean_fitness']}",
        f"- final mean_fitness（最终平均适应度）: {final['mean_fitness']}",
        f"- best mean_fitness（历史最佳平均适应度）: {best.get('mean_fitness')}",
        f"- generation 0 target_ir_exact_match（目标中间表示精确匹配）: {first['target_ir_exact_match_rate']}",
        f"- final target_ir_exact_match（最终目标中间表示精确匹配）: {final['target_ir_exact_match_rate']}",
        f"- best target_ir_exact_match（历史最佳目标中间表示精确匹配）: {best.get('target_ir_exact_match_rate')}",
        f"- final missing_layer_rate（最终缺层率）: {final['missing_layer_rate']}",
        "",
        "## Threshold Events（阈值事件）",
        "",
        f"- freeze events（冻结事件）: {curriculum['freeze_events']}",
        f"- threshold anneal events（阈值退火事件）: {curriculum['threshold_anneal_events']}",
        f"- threshold block events（阈值阻塞事件）: {curriculum['threshold_block_events']}",
        f"- frozen_threshold_by_layer（各层冻结阈值）: {curriculum['frozen_threshold_by_layer']}",
        "",
        "## support_gate（支持/拒绝门）",
        "",
        f"- threshold history（阈值历史）: {support_state.get('threshold_history', [])}",
        f"- winner accuracy（赢家准确率）: {final.get('per_layer_winner_accuracy', {}).get('support_gate')}",
        f"- layer_recall@k（层级候选召回）: {final.get('per_layer_recall_at_k', {}).get('support_gate')}",
        f"- confusion matrix（混淆矩阵）: {final.get('support_gate_confusion_matrix')}",
        f"- false reject supported（误拒支持样本）: {final.get('support_gate_false_reject_count')}",
        f"- false accept unsupported（误接收不支持样本）: {final.get('support_gate_false_accept_count')}",
        "",
        "## Per-Layer Counts（分层整数正确数）",
        "",
    ]
    for layer, total in sorted(final.get("per_layer_total_count", {}).items()):
        lines.append(
            f"- {layer}: actual_correct（实际正确数）={final['per_layer_correct_count'].get(layer)}, "
            f"required_correct（要求正确数）={final['per_layer_required_correct_count'].get(layer)}, total（总数）={total}"
        )
    lines.extend(["", "## Selection Problem Notes（选择问题提示）", ""])
    lines.extend(selection_notes or ["- none"])
    lines.extend(
        [
            "",
            "## Curves（曲线）",
            "",
            "- active_layer（当前训练层）: " + ", ".join(row["active_layer"] for row in metrics["metrics_by_generation"]),
            "- target_ir_exact_match（目标中间表示精确匹配）: " + ", ".join(str(row["target_ir_exact_match_rate"]) for row in metrics["metrics_by_generation"]),
            "- mean_fitness（平均适应度）: " + ", ".join(str(row["mean_fitness"]) for row in metrics["metrics_by_generation"]),
            "- missing_layer_rate（缺层率）: " + ", ".join(str(row["missing_layer_rate"]) for row in metrics["metrics_by_generation"]),
            "",
            "## Non-Claims（非主张）",
            "",
            "- This does not prove stable DarwinForge（达尔文进化炉） convergence.",
            "- This does not prove general program synthesis.",
            "- This does not train C source text.",
            "- This does not patch old source code.",
            "- This does not prove AGI, Transformer replacement, or hardware BPU implementation.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_confidence_gated_branchchain_toy(
    population_per_layer: int = 16,
    generations: int = 60,
    top_k_candidates: int = 3,
    seed: int = 42,
    compile_checks_per_generation: int = 0,
):
    GATED_DIR.mkdir(parents=True, exist_ok=True)
    trainer = CurriculumDarwinForgeTrainer(
        population_per_layer=population_per_layer,
        generations=generations,
        top_k_candidates=top_k_candidates,
        seed=seed,
        compile_checks_per_generation=compile_checks_per_generation,
    )
    metrics = trainer.train()
    candidate_records = metrics.pop("candidate_records")
    metrics["guarded_branchchain"] = trainer.population.guarded_config.to_dict()
    GATED_METRICS_PATH.write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    GATED_REPORT_PATH.write_text(_confidence_gated_report_markdown(metrics), encoding="utf-8")
    GATED_CANDIDATES_PATH.write_text(
        "".join(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for record in candidate_records[-200:]),
        encoding="utf-8",
    )
    metrics["report_path"] = str(GATED_REPORT_PATH)
    metrics["candidates_path"] = str(GATED_CANDIDATES_PATH)
    return metrics


def _confidence_gated_report_markdown(metrics):
    first = metrics["metrics_by_generation"][0]
    final = metrics["metrics_by_generation"][-1]
    best = metrics["hall_of_fame"]["best_metrics"]
    thresholds = {
        layer: config["continue_threshold"]
        for layer, config in metrics["guarded_branchchain"]["layer_gate_configs"].items()
    }
    lines = [
        "# v0.6.3 Confidence-Gated Guarded BranchChain（置信度守卫式带守卫分支链） Report",
        "",
        "support_gate（支持/拒绝门） remains for compatibility but is downgraded to an ordinary BranchChain（分支链） layer.",
        "",
        "## No-Confidence Rejection（无置信拒绝） Summary",
        "",
        f"- no_confidence_reject_count（无置信拒绝数）: {final['no_confidence_reject_count']}",
        f"- correct_no_confidence_reject_count（正确无置信拒绝数）: {final['correct_no_confidence_reject_count']}",
        f"- wrong_no_confidence_reject_count（错误无置信拒绝数）: {final['wrong_no_confidence_reject_count']}",
        f"- typed_reject_count（类型化拒绝数）: {final['typed_reject_count']}",
        f"- false_accept_unsupported_count（误接收不支持数）: {final['false_accept_unsupported_count']}",
        f"- false_reject_supported_count（误拒支持数）: {final['false_reject_supported_count']}",
        f"- rejected_by_layer_distribution（拒绝层分布）: {final['rejected_by_layer_distribution']}",
        f"- continue_threshold by layer（分层继续阈值）: {thresholds}",
        "",
        "## Final vs Best（最终与历史最佳）",
        "",
        f"- generation 0 target_ir_exact_match（目标中间表示精确匹配）: {first['target_ir_exact_match_rate']}",
        f"- final target_ir_exact_match（最终目标中间表示精确匹配）: {final['target_ir_exact_match_rate']}",
        f"- best target_ir_exact_match（历史最佳目标中间表示精确匹配）: {best.get('target_ir_exact_match_rate')}",
        f"- final missing_layer_rate（最终缺层率）: {final['missing_layer_rate']}",
        "",
        "## Per-Layer Gate Metrics（分层守卫指标）",
        "",
        f"- per_layer_reject_count（分层拒绝数）: {final['per_layer_reject_count']}",
        f"- per_layer_continue_rate（分层继续率）: {final['per_layer_continue_rate']}",
        f"- confidence_margin_by_layer（分层置信度间隔）: {final['confidence_margin_by_layer']}",
        "",
        "## Non-Claims（非主张）",
        "",
        "- This does not prove stable DarwinForge（达尔文进化炉） convergence.",
        "- This does not prove general program synthesis.",
        "- This does not train C source text.",
        "- This does not patch old source code.",
        "- This does not prove AGI, Transformer replacement, or hardware BPU implementation.",
    ]
    return "\n".join(lines) + "\n"


def run_architecture_aligned_dataset_toy(
    population_per_layer: int = 16,
    generations: int = 60,
    top_k_candidates: int = 3,
    seed: int = 42,
    compile_checks_per_generation: int = 0,
):
    ARCH_ALIGNED_DIR.mkdir(parents=True, exist_ok=True)
    old_dataset = build_branchchain_toy_dataset()
    new_dataset = build_architecture_aligned_toy_dataset()
    old_metrics, _old_records, _old_trainer = _train_dataset_for_v064(
        old_dataset,
        population_per_layer,
        generations,
        top_k_candidates,
        seed,
        compile_checks_per_generation,
    )
    new_metrics, new_records, new_trainer = _train_dataset_for_v064(
        new_dataset,
        population_per_layer,
        generations,
        top_k_candidates,
        seed,
        compile_checks_per_generation,
    )
    new_summary = dataset_summary(new_dataset)
    final = new_metrics["metrics_by_generation"][-1]
    old_final = old_metrics["metrics_by_generation"][-1]
    comparison = {
        "old_target_ir_exact_match": old_final["target_ir_exact_match_rate"],
        "new_target_ir_exact_match": final["target_ir_exact_match_rate"],
        "old_false_reject_supported_count": old_final["false_reject_supported_count"],
        "new_false_reject_supported_count": final["false_reject_supported_count"],
        "old_language_target_reject_count": old_final.get("rejected_by_layer_distribution", {}).get("language_target", 0),
        "new_language_target_reject_count": final.get("rejected_by_layer_distribution", {}).get("language_target", 0),
    }
    ood_english = _ood_english_behavior(new_dataset, new_trainer, top_k_candidates)
    metrics = {
        "dataset_summary": new_summary,
        "old_dataset_size": len(old_dataset),
        "new_dataset_size": len(new_dataset),
        "old_metrics": _strip_candidate_records(old_metrics),
        "new_metrics": _strip_candidate_records(new_metrics),
        "comparison": comparison,
        "ood_english_rejection_behavior": ood_english,
    }
    ARCH_ALIGNED_METRICS_PATH.write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    ARCH_ALIGNED_REPORT_PATH.write_text(_architecture_aligned_report_markdown(metrics), encoding="utf-8")
    ARCH_ALIGNED_CANDIDATES_PATH.write_text(
        "".join(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for record in new_records[-200:]),
        encoding="utf-8",
    )
    metrics["report_path"] = str(ARCH_ALIGNED_REPORT_PATH)
    metrics["candidates_path"] = str(ARCH_ALIGNED_CANDIDATES_PATH)
    return metrics


def _train_dataset_for_v064(dataset, population_per_layer, generations, top_k_candidates, seed, compile_checks_per_generation):
    trainer = CurriculumDarwinForgeTrainer(
        population_per_layer=population_per_layer,
        generations=generations,
        top_k_candidates=top_k_candidates,
        seed=seed,
        compile_checks_per_generation=compile_checks_per_generation,
    )
    metrics = trainer.train(dataset)
    records = metrics.pop("candidate_records")
    metrics["guarded_branchchain"] = trainer.population.guarded_config.to_dict()
    return metrics, records, trainer


def _strip_candidate_records(metrics):
    return {key: value for key, value in metrics.items() if key != "candidate_records"}


def _ood_english_behavior(dataset, trainer, top_k):
    ood_indexes = [index for index, sample in enumerate(dataset) if sample.get("input_mode") == "ood_english"]
    if not ood_indexes:
        return {"ood_english_count": 0, "rejected_count": 0, "accepted_count": 0}
    rejected = 0
    for index in ood_indexes:
        task = dataset[index]
        features = extract_surface_features(task["input_text"])
        records = []
        for genome in trainer.population.sample_candidate_paths(features, top_k=top_k):
            phenotype = trainer.synthesis.synthesize(genome, features)
            fitness = compute_fitness(genome, phenotype, task, sandbox_optional=False)
            records.append((fitness.total_fitness, phenotype))
        if records and max(records, key=lambda item: item[0])[1].unsupported_pred:
            rejected += 1
    return {
        "ood_english_count": len(ood_indexes),
        "rejected_count": rejected,
        "accepted_count": len(ood_indexes) - rejected,
        "behavior": "rejected" if rejected == len(ood_indexes) else "mixed",
    }


def _architecture_aligned_report_markdown(metrics):
    summary = metrics["dataset_summary"]
    old_final = metrics["old_metrics"]["metrics_by_generation"][-1]
    new_final = metrics["new_metrics"]["metrics_by_generation"][-1]
    best = metrics["new_metrics"]["hall_of_fame"]["best_metrics"]
    comparison = metrics["comparison"]
    lines = [
        "# v0.6.4 Architecture-Aligned Dataset（架构对齐数据集） Report",
        "",
        "This is a dataset realignment experiment for BranchChain（分支链） and TargetIR（目标中间表示） regeneration.",
        "",
        "## Dataset Summary（数据集摘要）",
        "",
        f"- dataset size（数据集规模）: {summary['dataset_size']}",
        f"- input_mode counts（输入模式计数）: {summary['input_mode_counts']}",
        f"- paraphrase_group counts（复述组计数）: {summary['paraphrase_group_counts']}",
        f"- supported count（支持样本数）: {summary['supported_count']}",
        f"- OOD count（分布外样本数）: {summary['ood_count']}",
        f"- language_target distribution（目标语言分布）: {summary['language_target_distribution']}",
        "",
        "## Old vs New Dataset Comparison（旧/新数据集对比）",
        "",
        f"- old toy target_ir_exact_match（旧目标中间表示精确匹配）: {comparison['old_target_ir_exact_match']}",
        f"- new architecture-aligned target_ir_exact_match（新架构对齐目标中间表示精确匹配）: {comparison['new_target_ir_exact_match']}",
        f"- old false_reject_supported_count（旧误拒支持数）: {comparison['old_false_reject_supported_count']}",
        f"- new false_reject_supported_count（新误拒支持数）: {comparison['new_false_reject_supported_count']}",
        f"- old language_target reject count（旧目标语言层拒绝数）: {comparison['old_language_target_reject_count']}",
        f"- new language_target reject count（新目标语言层拒绝数）: {comparison['new_language_target_reject_count']}",
        "",
        "## Rejection and Missing-Layer Metrics（拒绝与缺层指标）",
        "",
        f"- no_confidence_reject_count（无置信拒绝数）: {new_final['no_confidence_reject_count']}",
        f"- correct_no_confidence_reject_count（正确无置信拒绝数）: {new_final['correct_no_confidence_reject_count']}",
        f"- wrong_no_confidence_reject_count（错误无置信拒绝数）: {new_final['wrong_no_confidence_reject_count']}",
        f"- false_accept_unsupported_count（误接收不支持数）: {new_final['false_accept_unsupported_count']}",
        f"- false_reject_supported_count（误拒支持数）: {new_final['false_reject_supported_count']}",
        f"- true_missing_layer_rate（真正缺层率）: {new_final['true_missing_layer_rate']}",
        f"- early_reject_short_path_rate（早停短路径率）: {new_final['early_reject_short_path_rate']}",
        f"- final target_ir_exact_match（最终目标中间表示精确匹配）: {new_final['target_ir_exact_match_rate']}",
        f"- best target_ir_exact_match（最佳目标中间表示精确匹配）: {best['target_ir_exact_match_rate']}",
        "",
        "## OOD Evaluation（分布外评测）",
        "",
        f"- OOD english rejection behavior（英语分布外拒绝行为）: {metrics['ood_english_rejection_behavior']}",
        "",
        "## Non-Claims（非主张）",
        "",
        "- This does not prove stable DarwinForge（达尔文进化炉） convergence.",
        "- This does not prove general program synthesis.",
        "- This does not train C source text.",
        "- This does not patch old source code.",
        "- This does not prove AGI, Transformer replacement, or hardware BPU implementation.",
        "- This is a dataset realignment experiment.",
    ]
    return "\n".join(lines) + "\n"


def run_paraphrase_invariant_targetir_toy(
    population_per_layer: int = 16,
    generations: int = 80,
    top_k_candidates: int = 3,
    seed: int = 42,
    compile_checks_per_generation: int = 0,
):
    PARAPHRASE_DIR.mkdir(parents=True, exist_ok=True)
    dataset = build_architecture_aligned_toy_dataset()
    trainer = ParaphraseInvariantDarwinForgeTrainer(
        population_per_layer=population_per_layer,
        generations=generations,
        top_k_candidates=top_k_candidates,
        seed=seed,
        compile_checks_per_generation=compile_checks_per_generation,
    )
    metrics = trainer.train(dataset)
    candidate_records = metrics.pop("candidate_records")
    PARAPHRASE_METRICS_PATH.write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    PARAPHRASE_REPORT_PATH.write_text(_paraphrase_invariant_report_markdown(metrics), encoding="utf-8")
    PARAPHRASE_CANDIDATES_PATH.write_text(
        "".join(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for record in candidate_records[-240:]),
        encoding="utf-8",
    )
    metrics["report_path"] = str(PARAPHRASE_REPORT_PATH)
    metrics["candidates_path"] = str(PARAPHRASE_CANDIDATES_PATH)
    return metrics


def _paraphrase_invariant_report_markdown(metrics):
    first = metrics["metrics_by_generation"][0]
    final = metrics["metrics_by_generation"][-1]
    best = metrics["best_metrics"]
    lines = [
        "# v0.6.5 Paraphrase-Invariant TargetIR Training（复述不变目标中间表示训练） Report",
        "",
        "This is a group-level DarwinForge（达尔文进化炉） scaffold for BranchChain（分支链）, AtomicSynthesis（原子结构合成）, and TargetIR（目标中间表示） convergence.",
        "",
        "## Dataset（数据集）",
        "",
        f"- dataset size（数据集规模）: {metrics['dataset_size']}",
        f"- supported paraphrase group count（支持复述组数量）: {metrics['supported_paraphrase_group_count']}",
        f"- OOD count（分布外数量）: {metrics['ood_count']}",
        f"- input_mode counts（输入模式计数）: {metrics['input_mode_counts']}",
        "",
        "## Sample-Level Metrics（单样本指标）",
        "",
        f"- generation 0 sample_target_ir_exact_match（第 0 代单样本目标中间表示精确匹配）: {first['sample_target_ir_exact_match']}",
        f"- final sample_target_ir_exact_match（最终单样本目标中间表示精确匹配）: {final['sample_target_ir_exact_match']}",
        f"- best sample_target_ir_exact_match（最佳单样本目标中间表示精确匹配）: {best['sample_target_ir_exact_match']}",
        "",
        "## Group-Level Metrics（组级指标）",
        "",
        f"- generation 0 group_targetir_consistency（第 0 代组内一致性）: {first['group_targetir_consistency']}",
        f"- final group_targetir_consistency（最终组内一致性）: {final['group_targetir_consistency']}",
        f"- best group_targetir_consistency（最佳组内一致性）: {best['group_targetir_consistency']}",
        f"- generation 0 group_targetir_exact_match（第 0 代组内目标中间表示正确率）: {first['group_targetir_exact_match']}",
        f"- final group_targetir_exact_match（最终组内目标中间表示正确率）: {final['group_targetir_exact_match']}",
        f"- best group_targetir_exact_match（最佳组内目标中间表示正确率）: {best['group_targetir_exact_match']}",
        f"- cross_mode_consistency（跨输入模式一致性）: {final['cross_mode_consistency']}",
        f"- paraphrase_collapse_rate（复述坍缩率）: {final['paraphrase_collapse_rate']}",
        f"- supported_all_rejected_group_count（支持组全拒绝数量）: {final['supported_all_rejected_group_count']}",
        f"- group_inconsistent_count（组内不一致数量）: {final['group_inconsistent_count']}",
        "",
        "## OOD Evaluation（分布外评测）",
        "",
        f"- ood_rejection_rate（分布外拒绝率）: {final['ood_rejection_rate']}",
        f"- ood_false_accept_rate（分布外误接收率）: {final['ood_false_accept_rate']}",
        "",
        "## Representative Group Predictions（代表性复述组预测）",
        "",
    ]
    for row in final["representative_group_predictions"][:6]:
        lines.append(f"- {row['group_id']}: target={row['target_ir']}, predicted={row['predicted_targetirs']}, exact={row['exact']}, consistent={row['consistent']}")
    lines.extend(
        [
            "",
            "## Non-Claims（非主张）",
            "",
            "- This does not prove stable DarwinForge（达尔文进化炉） convergence.",
            "- This does not prove general program synthesis.",
            "- This does not train C source text.",
            "- This does not patch old source code.",
            "- This does not prove AGI, Transformer replacement, or hardware BPU implementation.",
            "- This is a Paraphrase-Invariant TargetIR Training（复述不变目标中间表示训练） scaffold.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_hindsight_branch_reranking_toy(
    population_per_layer: int = 16,
    generations: int = 80,
    top_k_candidates: int = 3,
    beam_width: int = 5,
    seed: int = 42,
    compile_checks_per_generation: int = 0,
):
    RERANK_DIR.mkdir(parents=True, exist_ok=True)
    dataset = build_architecture_aligned_toy_dataset()
    trainer = HindsightReRankingDarwinForgeTrainer(
        population_per_layer=population_per_layer,
        generations=generations,
        top_k_candidates=top_k_candidates,
        beam_width=beam_width,
        seed=seed,
        compile_checks_per_generation=compile_checks_per_generation,
    )
    metrics = trainer.train(dataset)
    candidate_records = metrics.pop("candidate_records")
    pruning_candidates = metrics.get("pruning_candidates", [])
    RERANK_METRICS_PATH.write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    RERANK_REPORT_PATH.write_text(_hindsight_reranking_report_markdown(metrics), encoding="utf-8")
    RERANK_CANDIDATES_PATH.write_text(
        "".join(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for record in candidate_records[-240:]),
        encoding="utf-8",
    )
    RERANK_PRUNING_PATH.write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in pruning_candidates),
        encoding="utf-8",
    )
    metrics["report_path"] = str(RERANK_REPORT_PATH)
    metrics["candidates_path"] = str(RERANK_CANDIDATES_PATH)
    metrics["pruning_candidates_path"] = str(RERANK_PRUNING_PATH)
    return metrics


def _hindsight_reranking_report_markdown(metrics):
    first = metrics["metrics_by_generation"][0]
    final = metrics["metrics_by_generation"][-1]
    best = metrics["best_metrics"]
    lines = [
        "# v0.6.6 Hindsight Branch Re-Ranking（回看式分支重排） Report",
        "",
        "This is a Group Beam Selection（组级束搜索） scaffold over top-k BranchPath（分支路径） candidates. It uses TargetIR（目标中间表示） and Paraphrase Group（复述组） feedback after prediction.",
        "",
        "## Dataset Summary（数据集摘要）",
        "",
        f"- dataset size（数据集规模）: {metrics['dataset_size']}",
        f"- supported group count（支持复述组数量）: {metrics['supported_group_count']}",
        f"- OOD count（分布外数量）: {metrics['ood_count']}",
        f"- top_k_candidates（候选保留数量）: {metrics['top_k_candidates']}",
        f"- beam_width（束宽）: {metrics['beam_width']}",
        "",
        "## Single Winner vs Re-Ranked vs Group Beam（单赢家 / 重排 / 组级束搜索）",
        "",
        f"- generation 0 single_winner_sample_exact_match（第 0 代单赢家精确匹配）: {first['single_winner_sample_exact_match']}",
        f"- final single_winner_sample_exact_match（最终单赢家精确匹配）: {final['single_winner_sample_exact_match']}",
        f"- final reranked_sample_exact_match（最终重排单样本精确匹配）: {final['reranked_sample_exact_match']}",
        f"- final group_beam_exact_match（最终组级束搜索精确匹配）: {final['group_beam_exact_match']}",
        f"- group_beam_consistency（组级束搜索一致性）: {final['group_beam_consistency']}",
        "",
        "## Candidate Quadrants（候选四象限）",
        "",
        f"- candidate_quadrant_counts（候选四象限计数）: {final['candidate_quadrant_counts']}",
        f"- low_score_correct_count（低分正确候选数量）: {final['low_score_correct_count']}",
        f"- high_score_wrong_count（高分错误候选数量）: {final['high_score_wrong_count']}",
        f"- rerank_improvement_count（重排改进数量）: {final['rerank_improvement_count']}",
        f"- rerank_regression_count（重排退化数量）: {final['rerank_regression_count']}",
        "",
        "## Branch Pruning（分支剪枝）",
        "",
        f"- wrong_consistent_group_count（一致但错误组数量）: {final['wrong_consistent_group_count']}",
        f"- pruning_candidate_count（剪枝候选数量）: {final['pruning_candidate_count']}",
        f"- collapse_penalty_hits（坍缩惩罚触发次数）: {final['collapse_penalty_hits']}",
        "",
        "## OOD Evaluation（分布外评测）",
        "",
        f"- ood_rejection_rate（分布外拒绝率）: {final['ood_rejection_rate']}",
        f"- ood_false_accept_rate（分布外误接收率）: {final['ood_false_accept_rate']}",
        "",
        "## Correct-Low-Score Candidate（低分正确候选） Examples",
        "",
    ]
    for item in final["low_score_correct_examples"][:3]:
        lines.append(f"- {item['sample_id']}: original_rank={item['original_rank']}, rerank_rank={item['rerank_rank']}, pred={item['target_ir_pred']}")
    lines.extend(["", "## Wrong-High-Score Candidate（高分错误候选） Examples", ""])
    for item in final["high_score_wrong_examples"][:3]:
        lines.append(f"- {item['sample_id']}: original_score={item['original_score']}, pred={item['target_ir_pred']}, true={item['target_ir_true']}")
    lines.extend(["", "## Non-Claims（非主张）", ""])
    lines.extend(
        [
            "- This does not prove stable DarwinForge（达尔文进化炉） convergence.",
            "- This does not prove general program synthesis.",
            "- This does not train C source text.",
            "- This does not patch old source code.",
            "- This does not prove AGI, Transformer replacement, or hardware BPU implementation.",
            "- This is a Hindsight Branch Re-Ranking（回看式分支重排） scaffold.",
        ]
    )
    return "\n".join(lines) + "\n"
