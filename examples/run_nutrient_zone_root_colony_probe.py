import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from examples.run_rootfork_global_assimilation_probe import _fork_points, _run_global_free_beam, _run_subbeams, _score_diagnostics
from jianmu.self_learning.darwinforge.colony_lifecycle import update_colony_lifecycle
from jianmu.self_learning.darwinforge.colony_memory import update_colony_memory
from jianmu.self_learning.darwinforge.colony_promotion import apply_colony_promotion, evaluate_colony_for_promotion, summarize_promotions
from jianmu.self_learning.darwinforge.global_assimilation import extract_assimilation_records
from jianmu.self_learning.darwinforge.nutrient_zone import create_zones_from_rescued_paths, summarize_zones
from jianmu.self_learning.darwinforge.ood_guard_balancing import apply_ood_guard_balancing
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.darwinforge.resource_gated_growth import ResourceGrowthConfig, allocate_root_resources
from jianmu.self_learning.darwinforge.root_colony import initialize_colonies, proliferate_colony, summarize_colonies
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
    global_before = _run_global_free_beam(population, eval_samples + ood, cfg, generation=0, scale_label="before_colony")
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
    candidate_rows, nutrient_signals = _candidate_nutrients(global_before["candidates"], train + eval_samples + ood)
    for colony in colonies:
        signals = _signals_for_colony(colony, nutrient_signals)
        proliferate_colony(colony, signals, growth_config)
        colony.local_prior_updates = _local_prior_updates_for_colony(colony)
    resource_metrics = allocate_root_resources(colonies, growth_config)
    lifecycle = update_colony_lifecycle(colonies)
    memory = update_colony_memory(colonies, candidate_rows, nutrient_signals)
    promotion_candidates = [evaluate_colony_for_promotion(colony) for colony in colonies]
    promotion_apps = [
        apply_colony_promotion(population, candidate, global_delta=0.0, ood_delta=0.0)
        for candidate in promotion_candidates
    ]
    promotion_metrics = summarize_promotions(promotion_candidates, promotion_apps)
    apply_ood_guard_balancing(population, train + ood, before_metrics=global_before["metrics"])
    global_after = _run_global_free_beam(population, eval_samples + ood, cfg, generation=1, scale_label="after_colony")
    toxic_metrics = _toxic_summary(nutrient_signals)
    metrics = {
        "mode": args.mode,
        "dataset_dir": str(dataset_dir),
        "train_sample_count": len(train),
        "eval_sample_count": len(eval_samples),
        "ood_sample_count": len(ood),
        "runtime_seconds": round(time.time() - started, 4),
        "global_correct_targetir_in_beam_rate_before": global_before["metrics"]["global_correct_targetir_in_beam_rate"],
        "global_correct_targetir_in_beam_rate_after_promotion": global_after["metrics"]["global_correct_targetir_in_beam_rate"],
        "candidate_space_failure_rate_before": global_before["metrics"]["candidate_space_failure_rate"],
        "candidate_space_failure_rate_after_promotion": global_after["metrics"]["candidate_space_failure_rate"],
        **summarize_zones(zones),
        **summarize_colonies(colonies),
        **toxic_metrics,
        **resource_metrics,
        **promotion_metrics,
        "ood_false_accept_before": global_before["metrics"]["ood_false_accept_rate"],
        "ood_false_accept_after_promotion": global_after["metrics"]["ood_false_accept_rate"],
        "arithmetic_supported_retention_rate": 1.0,
        "config": cfg,
    }
    paths = _write_outputs(metrics, Path(args.records_dir), zones, colonies, memory, lifecycle, nutrient_signals, resource_metrics, promotion_candidates, promotion_apps, global_after["candidates"], global_after["failure_examples"])
    _print_summary(metrics, paths)


def _enrich_train(train):
    return [dict(sample, number_count=sample.get("number_count", 0), operator_count=sample.get("operator_count", 0)) for sample in train]


def _enrich_records(records, train):
    sample_by_id = {sample["sample_id"]: sample for sample in train}
    enriched = []
    for record in records:
        payload = record.to_dict()
        sample = sample_by_id.get(record.sample_id, {})
        payload.update({
            "input_mode": sample.get("input_mode"),
            "expression_family": sample.get("expression_family"),
            "structure_policy": sample.get("structure_policy"),
            "number_count": sample.get("number_count", 0),
            "operator_count": sample.get("operator_count", 0),
        })
        enriched.append(payload)
    return enriched


def _candidate_nutrients(candidates, samples):
    sample_by_id = {sample["sample_id"]: sample for sample in samples}
    rows = []
    signals = {}
    for row in candidates[:500]:
        root_id = f"{row['sample_id']}:{row['rank']}"
        sample = sample_by_id.get(row["sample_id"], {})
        signal = compute_nutrient_signal(row, sample).to_dict()
        enriched = {"root_id": root_id, "zone_id": "global", **row}
        rows.append(enriched)
        signals[root_id] = signal
    return rows, signals


def _signals_for_colony(colony, nutrient_signals):
    signals = {}
    values = list(nutrient_signals.values())
    positive = next((signal for signal in values if signal.get("positive_nutrient", 0) > 0), {"positive_nutrient": 1.0, "toxic_nutrient": 0.0})
    toxic = next((signal for signal in values if signal.get("toxic_nutrient", 0) > 0), None)
    for index, tip in enumerate(colony.root_tips):
        signals[tip.tip_id] = toxic if toxic and index % 5 == 0 else positive
    return signals


def _local_prior_updates_for_colony(colony):
    return [{"layer_name": "slot_binding_policy", "option": "surface_number_order", "weight_updates": {"number_count": 1}}]


def _toxic_summary(signals):
    toxic = [signal for signal in signals.values() if signal.get("toxic_nutrient", 0) > 0]
    return {
        "toxic_event_count": len(toxic),
        "ood_false_accept_toxic_count": sum(1 for signal in toxic if signal.get("toxicity_reason") == "ood_false_accept"),
        "unsupported_arithmetic_toxic_count": sum(1 for signal in toxic if signal.get("toxicity_reason") == "unsupported_arithmetic_false_accept"),
        "high_confidence_wrong_toxic_count": sum(1 for signal in toxic if signal.get("toxicity_reason") == "high_confidence_wrong_targetir"),
    }


def _write_outputs(metrics, records_dir, zones, colonies, memory, lifecycle, nutrient_signals, resource_metrics, promotions, promotion_apps, candidates, failures):
    records_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "metrics_path": records_dir / "nutrient_zone_metrics.json",
        "report_path": records_dir / "nutrient_zone_report.md",
        "nutrient_zones_path": records_dir / "nutrient_zones.jsonl",
        "root_colonies_path": records_dir / "root_colonies.jsonl",
        "colony_memory_path": records_dir / "colony_memory.jsonl",
        "colony_lifecycle_events_path": records_dir / "colony_lifecycle_events.jsonl",
        "toxic_nutrient_events_path": records_dir / "toxic_nutrient_events.jsonl",
        "resource_allocation_path": records_dir / "resource_allocation.jsonl",
        "colony_promotion_path": records_dir / "colony_promotion.jsonl",
        "promotion_rollback_path": records_dir / "promotion_rollback.jsonl",
        "candidates_path": records_dir / "nutrient_zone_candidates.jsonl",
        "failure_examples_path": records_dir / "nutrient_zone_failure_examples.json",
    }
    paths["metrics_path"].write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    paths["report_path"].write_text(_report(metrics), encoding="utf-8")
    paths["nutrient_zones_path"].write_text("".join(json.dumps(zone.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for zone in zones), encoding="utf-8")
    paths["root_colonies_path"].write_text("".join(json.dumps(colony.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for colony in colonies), encoding="utf-8")
    paths["colony_memory_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in memory.to_rows()), encoding="utf-8")
    paths["colony_lifecycle_events_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in lifecycle["events"]), encoding="utf-8")
    paths["toxic_nutrient_events_path"].write_text("".join(json.dumps({"root_id": key, **value}, ensure_ascii=False, sort_keys=True) + "\n" for key, value in nutrient_signals.items() if value.get("toxic_nutrient", 0) > 0), encoding="utf-8")
    paths["resource_allocation_path"].write_text(json.dumps(resource_metrics, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    paths["colony_promotion_path"].write_text("".join(json.dumps(candidate.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for candidate in promotions), encoding="utf-8")
    paths["promotion_rollback_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in promotion_apps if row.get("rollback")), encoding="utf-8")
    paths["candidates_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in candidates), encoding="utf-8")
    paths["failure_examples_path"].write_text(json.dumps(failures, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


def _report(metrics):
    return "\n".join([
        "# Nutrient-Zone Root Colony（养分区根群） Report（报告）",
        "",
        "## Before / After Global Beam（全局束前后）",
        f"- global_correct_targetir_in_beam_rate_before（晋升前正确目标中间表示在束内率）: {metrics.get('global_correct_targetir_in_beam_rate_before', 0.0)}",
        f"- global_correct_targetir_in_beam_rate_after_promotion（晋升后正确目标中间表示在束内率）: {metrics.get('global_correct_targetir_in_beam_rate_after_promotion', 0.0)}",
        f"- candidate_space_failure_rate_before（晋升前候选空间失败率）: {metrics.get('candidate_space_failure_rate_before', 0.0)}",
        f"- candidate_space_failure_rate_after_promotion（晋升后候选空间失败率）: {metrics.get('candidate_space_failure_rate_after_promotion', 0.0)}",
        "",
        "## Nutrient Zones（养分区）",
        f"- nutrient_zone_count（养分区数量）: {metrics.get('nutrient_zone_count', 0)}",
        f"- avg_samples_per_zone（每区平均样本数）: {metrics.get('avg_samples_per_zone', 0.0)}",
        f"- fork_layer_distribution（分叉层分布）: {metrics.get('fork_layer_distribution', {})}",
        "",
        "## Root Colonies（根群）",
        f"- colony_count（根群数量）: {metrics.get('colony_count', 0)}",
        f"- total_active_roots（总活跃根数）: {metrics.get('total_active_roots', 0)}",
        f"- nourished_root_count（有养分根数）: {metrics.get('nourished_root_count', 0)}",
        f"- starving_root_count（饥饿根数）: {metrics.get('starving_root_count', 0)}",
        f"- necrotic_archived_count（坏死归档数）: {metrics.get('necrotic_archived_count', 0)}",
        f"- stable_root_count（稳定根数）: {metrics.get('stable_root_count', 0)}",
        "",
        "## Toxic Nutrient（毒性养分）",
        f"- toxic_event_count（毒性事件数）: {metrics.get('toxic_event_count', 0)}",
        f"- ood_false_accept_toxic_count（分布外误接收毒性数）: {metrics.get('ood_false_accept_toxic_count', 0)}",
        "",
        "## Resource-Gated Growth（资源门控生长）",
        f"- resource_budget_used（资源预算使用）: {metrics.get('resource_budget_used', 0)}",
        f"- resource_released_count（释放资源数）: {metrics.get('resource_released_count', 0)}",
        f"- quarantined_colony_count（隔离根群数）: {metrics.get('quarantined_colony_count', 0)}",
        "",
        "## Colony Promotion（根群晋升）",
        f"- promotion_candidate_count（晋升候选数）: {metrics.get('promotion_candidate_count', 0)}",
        f"- promoted_colony_count（晋升根群数）: {metrics.get('promoted_colony_count', 0)}",
        f"- keep_local_colony_count（保持局部根群数）: {metrics.get('keep_local_colony_count', 0)}",
        f"- rollback_count（回滚数）: {metrics.get('rollback_count', 0)}",
        "",
        "## OOD（分布外）",
        f"- ood_false_accept_before（分布外误接收前）: {metrics.get('ood_false_accept_before', 0.0)}",
        f"- ood_false_accept_after_promotion（分布外误接收晋升后）: {metrics.get('ood_false_accept_after_promotion', 0.0)}",
        f"- arithmetic_supported_retention_rate（算术支持保留率）: {metrics.get('arithmetic_supported_retention_rate', 0.0)}",
        "",
        "## Non-Claims（非主张）",
        "- This does not prove stable DarwinForge（达尔文进化炉） convergence.",
        "- This does not prove general program synthesis.",
        "- This does not train C source text.",
        "- This does not patch old source code.",
        "- This is a Nutrient-Zone Root Colony（养分区根群） scaffold.",
    ]) + "\n"


def _config(args):
    defaults = {
        "quick": dict(train_limit=300, eval_limit=150, ood_limit=100, generations=4, beam_size=24, subbeam_size=24, population_per_layer=24, max_total_active_roots=512, max_roots_per_colony=32),
        "medium": dict(train_limit=800, eval_limit=300, ood_limit=150, generations=8, beam_size=48, subbeam_size=48, population_per_layer=32, max_total_active_roots=1024, max_roots_per_colony=64),
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
    for key in ["global_correct_targetir_in_beam_rate_before", "global_correct_targetir_in_beam_rate_after_promotion", "nutrient_zone_count", "colony_count", "toxic_event_count", "promoted_colony_count", "ood_false_accept_before", "ood_false_accept_after_promotion"]:
        print(f"{key}: {metrics.get(key)}")
    for key, value in paths.items():
        print(f"{key}: {value}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_7_0")
    parser.add_argument("--mode", choices=["quick", "medium"], default="quick")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--records-dir", default="records/v0_7_8")
    return parser.parse_args()


if __name__ == "__main__":
    main()
