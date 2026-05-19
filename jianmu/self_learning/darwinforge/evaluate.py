import json
from pathlib import Path

from jianmu.self_learning.darwinforge.evolution import CurriculumDarwinForgeTrainer, DarwinForgeTrainer


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
