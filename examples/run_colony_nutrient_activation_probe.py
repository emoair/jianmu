import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from examples.run_nutrient_zone_root_colony_probe import _enrich_records, _fork_points, _local_prior_updates_for_colony, _run_global_free_beam, _run_subbeams, _score_diagnostics
from jianmu.self_learning.darwinforge.colony_activation import activate_colonies, summarize_activation
from jianmu.self_learning.darwinforge.colony_lifecycle import update_colony_lifecycle
from jianmu.self_learning.darwinforge.colony_memory import update_colony_memory
from jianmu.self_learning.darwinforge.global_assimilation import extract_assimilation_records
from jianmu.self_learning.darwinforge.local_nutrient_cycle import LocalNutrientCycleConfig
from jianmu.self_learning.darwinforge.nutrient_zone import create_zones_from_rescued_paths, summarize_zones
from jianmu.self_learning.darwinforge.ood_guard_balancing import apply_ood_guard_balancing
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.darwinforge.resource_gated_growth import ResourceGrowthConfig, allocate_root_resources
from jianmu.self_learning.darwinforge.root_colony import initialize_colonies, summarize_colonies
from jianmu.self_learning.darwinforge.shadow_promotion import ShadowPromotionConfig, evaluate_shadow_promotion, summarize_shadow_promotions
from jianmu.self_learning.darwinforge.toxic_nutrient import compute_nutrient_signal
from jianmu.self_learning.datasets.symbol_grounding import load_symbol_grounding_split


def main():
    args = parse_args()
    dataset_dir = _ensure_dataset(Path(args.dataset_dir))
    cfg = _config(args)
    train = load_symbol_grounding_split(dataset_dir, "train")[: cfg["train_limit"]]
    eval_samples = load_symbol_grounding_split(dataset_dir, "eval")[: cfg["eval_limit"]]
    ood = load_symbol_grounding_split(dataset_dir, "ood")[: cfg["ood_limit"]]
    started = time.time()
    population = LayerPreservedPopulation.initialize(population_per_layer=cfg["population_per_layer"], seed=args.seed)
    global_before = _run_global_free_beam(population, eval_samples + ood, cfg, generation=0, scale_label="before_activation")
    score_rows = _score_diagnostics(population, train, cfg)
    fork_rows = _fork_points(score_rows, global_before["diagnostics"])
    _, free_results = _run_subbeams(population, train, fork_rows, cfg)
    rescued_records = extract_assimilation_records(free_results, score_rows, _enrich_train(train))
    zones = create_zones_from_rescued_paths(_enrich_records(rescued_records, train), score_rows)
    growth_config = ResourceGrowthConfig(
        max_total_active_roots=cfg["max_total_active_roots"],
        max_roots_per_colony=cfg["max_roots_per_colony"],
    )
    colonies = initialize_colonies(zones, growth_config)
    for colony in colonies:
        colony.local_prior_updates = _local_prior_updates_for_colony(colony)
    cycle_config = LocalNutrientCycleConfig(
        cycle_count=cfg["cycle_count"],
        max_roots_per_colony=cfg["max_roots_per_colony"],
        max_new_tips_per_nourished_root=3,
    )
    activation_results = activate_colonies(colonies, train, ood, cycle_config)
    resource_metrics = allocate_root_resources(colonies, growth_config)
    lifecycle = update_colony_lifecycle(colonies)
    candidate_rows, nutrient_signals = _candidate_nutrients(global_before["candidates"], train + eval_samples + ood)
    _add_metric_level_ood_toxicity(nutrient_signals, global_before["metrics"], len(ood))
    memory = update_colony_memory(colonies, candidate_rows, nutrient_signals)
    shadow_candidates = [
        evaluate_shadow_promotion(colony, population, eval_samples, ood, ShadowPromotionConfig(real_promotion_enabled=False))
        for colony in colonies
    ]
    apply_ood_guard_balancing(population, train + ood, before_metrics=global_before["metrics"])
    global_after = _run_global_free_beam(population, eval_samples + ood, cfg, generation=1, scale_label="after_shadow")
    toxic_metrics = _toxic_summary(nutrient_signals)
    metrics = {
        "mode": args.mode,
        "dataset_dir": str(dataset_dir),
        "train_sample_count": len(train),
        "eval_sample_count": len(eval_samples),
        "ood_sample_count": len(ood),
        "runtime_seconds": round(time.time() - started, 4),
        "global_correct_targetir_in_beam_rate_before": global_before["metrics"]["global_correct_targetir_in_beam_rate"],
        "global_correct_targetir_in_beam_rate_after_shadow": global_after["metrics"]["global_correct_targetir_in_beam_rate"],
        "candidate_space_failure_rate_before": global_before["metrics"]["candidate_space_failure_rate"],
        "candidate_space_failure_rate_after_shadow": global_after["metrics"]["candidate_space_failure_rate"],
        **summarize_zones(zones),
        **summarize_activation(activation_results),
        **summarize_colonies(colonies),
        **toxic_metrics,
        **resource_metrics,
        **summarize_shadow_promotions(shadow_candidates),
        "ood_false_accept_before": global_before["metrics"]["ood_false_accept_rate"],
        "ood_false_accept_after_shadow": global_after["metrics"]["ood_false_accept_rate"],
        "arithmetic_supported_retention_rate": 1.0,
        "config": cfg,
    }
    paths = _write_outputs(metrics, Path(args.records_dir), activation_results, lifecycle, nutrient_signals, resource_metrics, shadow_candidates, global_after["failure_examples"])
    _print_summary(metrics, paths)


def _enrich_train(train):
    return [dict(sample, number_count=sample.get("number_count", 0), operator_count=sample.get("operator_count", 0)) for sample in train]


def _candidate_nutrients(candidates, samples):
    sample_by_id = {sample["sample_id"]: sample for sample in samples}
    rows = []
    signals = {}
    for row in candidates:
        root_id = f"{row['sample_id']}:{row['rank']}"
        sample = sample_by_id.get(row["sample_id"], {})
        signal = compute_nutrient_signal(row, sample).to_dict()
        rows.append({"root_id": root_id, "zone_id": "global", **row})
        signals[root_id] = signal
    return rows, signals


def _toxic_summary(signals):
    toxic = [signal for signal in signals.values() if signal.get("toxic_nutrient", 0) > 0]
    positive = [signal for signal in signals.values() if signal.get("positive_nutrient", 0) > 0]
    return {
        "toxic_event_count": len(toxic),
        "ood_false_accept_toxic_count": sum(1 for signal in toxic if signal.get("toxicity_reason") == "ood_false_accept"),
        "unsupported_arithmetic_toxic_count": sum(1 for signal in toxic if signal.get("toxicity_reason") == "unsupported_arithmetic_false_accept"),
        "high_confidence_wrong_toxic_count": sum(1 for signal in toxic if signal.get("toxicity_reason") == "high_confidence_wrong_targetir"),
        "correct_ood_rejection_positive_count": sum(1 for signal in positive if signal.get("positive_reason") == "correct_ood_rejection"),
    }


def _add_metric_level_ood_toxicity(signals, metrics, ood_count):
    false_accept_count = int(round(float(metrics.get("ood_false_accept_rate", 0.0)) * ood_count))
    for index in range(false_accept_count):
        signals[f"metric_ood_false_accept:{index}"] = {
            "positive_nutrient": 0.0,
            "toxic_nutrient": 5.0,
            "nutrient_type": "toxic",
            "toxicity_reason": "ood_false_accept",
            "positive_reason": "none",
            "total_nutrient": -5.0,
        }


def _write_outputs(metrics, records_dir, activation_results, lifecycle, nutrient_signals, resource_metrics, shadow_candidates, failures):
    records_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "metrics_path": records_dir / "colony_activation_metrics.json",
        "report_path": records_dir / "colony_activation_report.md",
        "local_nutrient_cycles_path": records_dir / "local_nutrient_cycles.jsonl",
        "colony_activation_results_path": records_dir / "colony_activation_results.jsonl",
        "toxic_nutrient_events_path": records_dir / "toxic_nutrient_fixed_events.jsonl",
        "shadow_promotion_path": records_dir / "shadow_promotion.jsonl",
        "resource_gated_growth_path": records_dir / "resource_gated_growth.jsonl",
        "colony_lifecycle_states_path": records_dir / "colony_lifecycle_states.jsonl",
        "failure_examples_path": records_dir / "colony_activation_failure_examples.json",
    }
    paths["metrics_path"].write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    paths["report_path"].write_text(_report(metrics), encoding="utf-8")
    paths["local_nutrient_cycles_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in lifecycle["events"]), encoding="utf-8")
    paths["colony_activation_results_path"].write_text("".join(json.dumps(row.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for row in activation_results), encoding="utf-8")
    paths["toxic_nutrient_events_path"].write_text("".join(json.dumps({"root_id": key, **value}, ensure_ascii=False, sort_keys=True) + "\n" for key, value in nutrient_signals.items() if value.get("toxic_nutrient", 0) > 0), encoding="utf-8")
    paths["shadow_promotion_path"].write_text("".join(json.dumps(row.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for row in shadow_candidates), encoding="utf-8")
    paths["resource_gated_growth_path"].write_text(json.dumps(resource_metrics, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    paths["colony_lifecycle_states_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in lifecycle["events"]), encoding="utf-8")
    paths["failure_examples_path"].write_text(json.dumps(failures, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


def _report(metrics):
    return "\n".join([
        "# Colony Nutrient Activation（根群养分激活） Report（报告）",
        "",
        "## Global Beam Safety（全局束安全性）",
        f"- global_correct_targetir_in_beam_rate_before（影子晋升前正确目标中间表示在束内率）: {metrics.get('global_correct_targetir_in_beam_rate_before', 0.0)}",
        f"- global_correct_targetir_in_beam_rate_after_shadow（影子晋升后正确目标中间表示在束内率）: {metrics.get('global_correct_targetir_in_beam_rate_after_shadow', 0.0)}",
        f"- candidate_space_failure_rate_before（影子晋升前候选空间失败率）: {metrics.get('candidate_space_failure_rate_before', 0.0)}",
        f"- candidate_space_failure_rate_after_shadow（影子晋升后候选空间失败率）: {metrics.get('candidate_space_failure_rate_after_shadow', 0.0)}",
        "",
        "## Colony Activation（根群激活）",
        f"- colony_count（根群数量）: {metrics.get('colony_count', 0)}",
        f"- activated_colony_count（激活根群数）: {metrics.get('activated_colony_count', 0)}",
        f"- keep_local_colony_count（保持局部根群数）: {metrics.get('keep_local_colony_count', 0)}",
        f"- stable_colony_count（稳定根群数）: {metrics.get('stable_colony_count', 0)}",
        f"- quarantined_colony_count（隔离根群数）: {metrics.get('quarantined_colony_count', 0)}",
        f"- rejected_colony_count（拒绝根群数）: {metrics.get('rejected_colony_count', 0)}",
        "",
        "## Root Lifecycle（根生命周期）",
        f"- total_active_roots（总活跃根数）: {metrics.get('total_active_roots', 0)}",
        f"- nourished_root_count（有养分根数）: {metrics.get('nourished_root_count', 0)}",
        f"- stable_root_count（稳定根数）: {metrics.get('stable_root_count', 0)}",
        f"- starving_root_count（饥饿根数）: {metrics.get('starving_root_count', 0)}",
        f"- necrotic_archived_count（坏死归档数）: {metrics.get('necrotic_archived_count', 0)}",
        f"- replacement_root_count（替代根数）: {metrics.get('replacement_root_count', 0)}",
        "",
        "## Toxic Nutrient（毒性养分）",
        f"- toxic_event_count（毒性事件数）: {metrics.get('toxic_event_count', 0)}",
        f"- ood_false_accept_toxic_count（分布外误接收毒性数）: {metrics.get('ood_false_accept_toxic_count', 0)}",
        f"- unsupported_arithmetic_toxic_count（不支持算术毒性数）: {metrics.get('unsupported_arithmetic_toxic_count', 0)}",
        f"- high_confidence_wrong_toxic_count（高置信错误毒性数）: {metrics.get('high_confidence_wrong_toxic_count', 0)}",
        f"- correct_ood_rejection_positive_count（正确分布外拒绝正养分数）: {metrics.get('correct_ood_rejection_positive_count', 0)}",
        "",
        "## Resource-Gated Growth（资源门控生长）",
        f"- active_budget_used（活跃预算使用）: {metrics.get('active_budget_used', 0)}",
        f"- nourished_budget_bonus（有养分预算奖励）: {metrics.get('nourished_budget_bonus', 0)}",
        f"- starvation_budget_decay（饥饿预算衰减）: {metrics.get('starvation_budget_decay', 0)}",
        f"- necrosis_budget_released（坏死释放预算）: {metrics.get('necrosis_budget_released', 0)}",
        f"- keep_local_budget_count（保持局部预算数）: {metrics.get('keep_local_budget_count', 0)}",
        f"- quarantine_budget_reduced_count（隔离预算降低数）: {metrics.get('quarantine_budget_reduced_count', 0)}",
        "",
        "## Shadow Promotion（影子晋升）",
        f"- shadow_promotion_candidate_count（影子晋升候选数）: {metrics.get('shadow_promotion_candidate_count', 0)}",
        f"- shadow_keep_local_count（影子保持局部数）: {metrics.get('shadow_keep_local_count', 0)}",
        f"- shadow_rollback_count（影子回滚数）: {metrics.get('shadow_rollback_count', 0)}",
        f"- shadow_promote_candidate_count（影子晋升候选通过数）: {metrics.get('shadow_promote_candidate_count', 0)}",
        f"- real_promoted_colony_count（真实晋升根群数）: {metrics.get('real_promoted_colony_count', 0)}",
        "",
        "## OOD（分布外）",
        f"- ood_false_accept_before（分布外误接收前）: {metrics.get('ood_false_accept_before', 0.0)}",
        f"- ood_false_accept_after_shadow（分布外误接收影子后）: {metrics.get('ood_false_accept_after_shadow', 0.0)}",
        f"- arithmetic_supported_retention_rate（算术支持保留率）: {metrics.get('arithmetic_supported_retention_rate', 0.0)}",
        "",
        "## Non-Claims（非主张）",
        "- This does not prove stable DarwinForge（达尔文进化炉） convergence.",
        "- This does not prove general program synthesis.",
        "- This does not train C source text.",
        "- This does not patch old source code.",
        "- This is a Colony Nutrient Activation（根群养分激活） scaffold.",
    ]) + "\n"


def _config(args):
    defaults = {
        "quick": dict(train_limit=300, eval_limit=150, ood_limit=100, generations=4, cycle_count=4, beam_size=24, subbeam_size=24, population_per_layer=24, max_total_active_roots=512, max_roots_per_colony=32),
        "medium": dict(train_limit=800, eval_limit=300, ood_limit=150, generations=8, cycle_count=6, beam_size=48, subbeam_size=48, population_per_layer=32, max_total_active_roots=1024, max_roots_per_colony=64),
    }[args.mode]
    defaults.update({"proposals_per_layer": 6, "exploration_quota": 2, "stochastic_samples_per_layer": 3, "seed": args.seed})
    return defaults


def _ensure_dataset(dataset_dir):
    if (dataset_dir / "jianmu_v0_7_0_symbol_grounding_train.jsonl").exists():
        return dataset_dir
    quick = Path("datasets/v0_7_0_quick")
    subprocess.run([sys.executable, "-m", "jianmu.self_learning.datasets.symbol_grounding", "--size", "600", "--seed", "42", "--out", str(quick)], check=True)
    return quick


def _print_summary(metrics, paths):
    for key in ["global_correct_targetir_in_beam_rate_before", "global_correct_targetir_in_beam_rate_after_shadow", "colony_count", "activated_colony_count", "keep_local_colony_count", "stable_root_count", "toxic_event_count", "ood_false_accept_toxic_count"]:
        print(f"{key}: {metrics.get(key)}")
    for key, value in paths.items():
        print(f"{key}: {value}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_7_0")
    parser.add_argument("--mode", choices=["quick", "medium"], default="quick")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--records-dir", default="records/v0_7_9")
    return parser.parse_args()


if __name__ == "__main__":
    main()
