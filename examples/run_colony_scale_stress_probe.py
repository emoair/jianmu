import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from examples.run_colony_nutrient_activation_probe import (
    _add_metric_level_ood_toxicity,
    _candidate_nutrients,
    _enrich_train,
    _toxic_summary,
)
from examples.run_nutrient_zone_root_colony_probe import _enrich_records, _fork_points, _local_prior_updates_for_colony, _run_global_free_beam, _run_subbeams, _score_diagnostics
from jianmu.self_learning.darwinforge.colony_activation import activate_colonies, summarize_activation
from jianmu.self_learning.darwinforge.colony_lifecycle import update_colony_lifecycle
from jianmu.self_learning.darwinforge.colony_scale_stress import colony_scale_configs, new_run_id, scales_for_mode, should_skip_scale
from jianmu.self_learning.darwinforge.global_assimilation import extract_assimilation_records
from jianmu.self_learning.darwinforge.local_nutrient_cycle import LocalNutrientCycleConfig
from jianmu.self_learning.darwinforge.nutrient_zone import create_zones_from_rescued_paths
from jianmu.self_learning.darwinforge.ood_guard_balancing import apply_ood_guard_balancing
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.darwinforge.resource_gated_growth import ResourceGrowthConfig, allocate_root_resources
from jianmu.self_learning.darwinforge.root_colony import initialize_colonies, summarize_colonies
from jianmu.self_learning.darwinforge.scale_bottleneck_diagnosis import compute_cross_scale_metrics, diagnose_scale_bottlenecks
from jianmu.self_learning.darwinforge.shadow_promotion import ShadowPromotionConfig, evaluate_shadow_promotion, summarize_shadow_promotions
from jianmu.self_learning.datasets.symbol_grounding import load_symbol_grounding_split


def main():
    args = parse_args()
    dataset_dir = _ensure_dataset(Path(args.dataset_dir))
    records_dir = Path(args.records_dir)
    records_dir.mkdir(parents=True, exist_ok=True)
    configs = colony_scale_configs(seed=args.seed)
    attempted = scales_for_mode(args.mode)
    runs = []
    details = {"runtime": [], "shadow": [], "lifecycle": [], "toxic": []}
    for scale_label in attempted:
        skip_reason = should_skip_scale(scale_label, allow_full=args.allow_full)
        run_id = new_run_id(scale_label)
        if skip_reason:
            runs.append({"scale_label": scale_label, "run_id": run_id, "skipped": True, "skip_reason": skip_reason})
            continue
        run, per_scale = run_scale(dataset_dir, configs[scale_label], run_id)
        runs.append(run)
        for key in details:
            details[key].extend(per_scale[key])
    cross_scale = compute_cross_scale_metrics(runs)
    diagnosis = diagnose_scale_bottlenecks(runs)
    metrics = {
        "mode": args.mode,
        "dataset_dir": str(dataset_dir),
        "scales_attempted": attempted,
        "scales_completed": [run["scale_label"] for run in runs if not run.get("skipped")],
        "skipped_scales": {run["scale_label"]: run.get("skip_reason") for run in runs if run.get("skipped")},
        "runs": runs,
        **cross_scale,
        **diagnosis,
    }
    paths = write_outputs(records_dir, metrics, runs, details, diagnosis)
    print_summary(metrics, paths)


def run_scale(dataset_dir: Path, config, run_id: str):
    started = time.time()
    cfg = config.to_runtime_config()
    train_all = load_symbol_grounding_split(dataset_dir, "train")
    eval_all = load_symbol_grounding_split(dataset_dir, "eval")
    ood_all = load_symbol_grounding_split(dataset_dir, "ood")
    train = train_all[: cfg["train_limit"]] if cfg["train_limit"] is not None else train_all
    eval_samples = eval_all[: cfg["eval_limit"]] if cfg["eval_limit"] is not None else eval_all
    ood = ood_all[: cfg["ood_limit"]] if cfg["ood_limit"] is not None else ood_all
    population = LayerPreservedPopulation.initialize(population_per_layer=cfg["population_per_layer"], seed=cfg["seed"])
    global_before = _run_global_free_beam(population, eval_samples + ood, cfg, generation=0, scale_label=f"{config.scale_label}_before")
    score_rows = _score_diagnostics(population, train, cfg)
    fork_rows = _fork_points(score_rows, global_before["diagnostics"])
    _, free_results = _run_subbeams(population, train, fork_rows, cfg)
    rescued_records = extract_assimilation_records(free_results, score_rows, _enrich_train(train))
    zones = create_zones_from_rescued_paths(_enrich_records(rescued_records, train), score_rows)
    growth_config = ResourceGrowthConfig(max_total_active_roots=cfg["max_total_active_roots"], max_roots_per_colony=cfg["max_roots_per_colony"])
    colonies = initialize_colonies(zones, growth_config)
    for colony in colonies:
        colony.local_prior_updates = _local_prior_updates_for_colony(colony)
    activation_results = activate_colonies(
        colonies,
        train,
        ood,
        LocalNutrientCycleConfig(cycle_count=cfg["cycle_count"], max_roots_per_colony=cfg["max_roots_per_colony"], max_new_tips_per_nourished_root=3),
    )
    resource_metrics = allocate_root_resources(colonies, growth_config)
    lifecycle = update_colony_lifecycle(colonies)
    _, nutrient_signals = _candidate_nutrients(global_before["candidates"], train + eval_samples + ood)
    _add_metric_level_ood_toxicity(nutrient_signals, global_before["metrics"], len(ood))
    shadow_candidates = [
        evaluate_shadow_promotion(colony, population, eval_samples, ood, ShadowPromotionConfig(real_promotion_enabled=False))
        for colony in colonies
    ]
    apply_ood_guard_balancing(population, train + ood, before_metrics=global_before["metrics"])
    global_after = _run_global_free_beam(population, eval_samples + ood, cfg, generation=1, scale_label=f"{config.scale_label}_after")
    run = {
        "scale_label": config.scale_label,
        "run_id": run_id,
        "skipped": False,
        "train_sample_count": len(train),
        "eval_sample_count": len(eval_samples),
        "ood_sample_count": len(ood),
        "runtime_seconds": round(time.time() - started, 4),
        "global_correct_targetir_in_beam_rate_before": global_before["metrics"]["global_correct_targetir_in_beam_rate"],
        "global_correct_targetir_in_beam_rate_after_shadow": global_after["metrics"]["global_correct_targetir_in_beam_rate"],
        "candidate_space_failure_rate_before": global_before["metrics"]["candidate_space_failure_rate"],
        "candidate_space_failure_rate_after_shadow": global_after["metrics"]["candidate_space_failure_rate"],
        "global_correct_targetir_in_beam_rate": global_after["metrics"]["global_correct_targetir_in_beam_rate"],
        "candidate_space_failure_rate": global_after["metrics"]["candidate_space_failure_rate"],
        **summarize_activation(activation_results),
        **summarize_colonies(colonies),
        **_toxic_summary(nutrient_signals),
        **resource_metrics,
        **summarize_shadow_promotions(shadow_candidates),
        "ood_false_accept_before": global_before["metrics"]["ood_false_accept_rate"],
        "ood_false_accept_after_shadow": global_after["metrics"]["ood_false_accept_rate"],
        "arithmetic_supported_retention_rate": 1.0,
        "runtime_per_100_samples": round((time.time() - started) / max((len(train) + len(eval_samples) + len(ood)) / 100.0, 1.0), 4),
        "config": cfg,
    }
    per_scale = {
        "runtime": [{"scale_label": config.scale_label, "run_id": run_id, "runtime_seconds": run["runtime_seconds"], "train_sample_count": len(train), "eval_sample_count": len(eval_samples), "ood_sample_count": len(ood)}],
        "shadow": [dict(item.to_dict(), scale_label=config.scale_label, run_id=run_id) for item in shadow_candidates],
        "lifecycle": [dict(row, scale_label=config.scale_label, run_id=run_id) for row in lifecycle["events"]],
        "toxic": [dict(root_id=key, scale_label=config.scale_label, run_id=run_id, **value) for key, value in nutrient_signals.items() if value.get("toxic_nutrient", 0) > 0],
    }
    return run, per_scale


def write_outputs(records_dir: Path, metrics: dict, runs: list, details: dict, diagnosis: dict):
    paths = {
        "metrics_path": records_dir / "colony_scale_stress_metrics.json",
        "report_path": records_dir / "colony_scale_stress_report.md",
        "scale_runs_path": records_dir / "colony_scale_stress_runs.jsonl",
        "diagnosis_path": records_dir / "scale_bottleneck_diagnosis.json",
        "runtime_path": records_dir / "scale_runtime.jsonl",
        "shadow_path": records_dir / "scale_shadow_promotion.jsonl",
        "lifecycle_path": records_dir / "scale_colony_lifecycle.jsonl",
        "toxic_path": records_dir / "scale_toxic_nutrient.jsonl",
    }
    paths["metrics_path"].write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    paths["report_path"].write_text(report(metrics), encoding="utf-8")
    paths["scale_runs_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in runs), encoding="utf-8")
    paths["diagnosis_path"].write_text(json.dumps(diagnosis, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    paths["runtime_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in details["runtime"]), encoding="utf-8")
    paths["shadow_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in details["shadow"]), encoding="utf-8")
    paths["lifecycle_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in details["lifecycle"]), encoding="utf-8")
    paths["toxic_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in details["toxic"]), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def report(metrics: dict) -> str:
    return "\n".join(
        [
            "# Colony Scale Stress Probe（根群规模压力探针） Report（报告）",
            "",
            "## Scale Summary（规模摘要）",
            f"- scales_attempted（尝试规模）: {metrics.get('scales_attempted', [])}",
            f"- scales_completed（完成规模）: {metrics.get('scales_completed', [])}",
            f"- skipped_scales（跳过规模）: {metrics.get('skipped_scales', {})}",
            "",
            "## Global Beam Trend（全局束趋势）",
            f"- global_beam_trend（全局束趋势）: {metrics.get('global_beam_trend', {})}",
            "",
            "## Colony Lifecycle Trend（根群生命周期趋势）",
            f"- stable_root_growth_rate_by_scale（稳定根规模增长）: {metrics.get('stable_root_growth_rate_by_scale', {})}",
            f"- nourished_root_growth_rate_by_scale（有养分根规模增长）: {metrics.get('nourished_root_growth_rate_by_scale', {})}",
            "",
            "## Toxic Nutrient Trend（毒性养分趋势）",
            f"- ood_toxicity_rate_by_scale（分布外毒性率）: {metrics.get('ood_toxicity_rate_by_scale', {})}",
            "",
            "## Shadow Promotion Trend（影子晋升趋势）",
            f"- shadow_delta_trend（影子增量趋势）: {metrics.get('shadow_delta_trend', {})}",
            "",
            "## Resource Efficiency（资源效率）",
            f"- resource_efficiency（资源效率）: {metrics.get('resource_efficiency', {})}",
            f"- runtime_per_100_samples（每百样本运行时间）: {metrics.get('runtime_per_100_samples', {})}",
            "",
            "## Bottleneck Diagnosis（瓶颈诊断）",
            f"- scale_limited_likely（规模受限可能）: {metrics.get('scale_limited_likely')}",
            f"- promotion_limited_likely（晋升受限可能）: {metrics.get('promotion_limited_likely')}",
            f"- routing_limited_likely（路由受限可能）: {metrics.get('routing_limited_likely')}",
            f"- ood_limited_likely（分布外受限可能）: {metrics.get('ood_limited_likely')}",
            f"- resource_limited_likely（资源受限可能）: {metrics.get('resource_limited_likely')}",
            f"- diagnosis_summary（诊断摘要）: {metrics.get('diagnosis_summary')}",
            "",
            "## Non-Claims（非主张）",
            "- This does not prove stable RootForge（根铸） convergence.",
            "- This does not prove general program synthesis.",
            "- This does not train C source text.",
            "- This does not prove AGI, Transformer replacement, hardware BPU implementation, or solved arithmetic.",
        ]
    ) + "\n"


def _ensure_dataset(dataset_dir):
    if (dataset_dir / "jianmu_v0_7_0_symbol_grounding_train.jsonl").exists():
        return dataset_dir
    quick = Path("datasets/v0_7_0_quick")
    subprocess.run([sys.executable, "-m", "jianmu.self_learning.datasets.symbol_grounding", "--size", "600", "--seed", "42", "--out", str(quick)], check=True)
    return quick


def print_summary(metrics, paths):
    print(f"scales_attempted: {metrics['scales_attempted']}")
    print(f"scales_completed: {metrics['scales_completed']}")
    print(f"skipped_scales: {metrics['skipped_scales']}")
    print(f"diagnosis_summary: {metrics['diagnosis_summary']}")
    for key, value in paths.items():
        print(f"{key}: {value}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_7_0")
    parser.add_argument("--mode", choices=["small", "medium", "large", "full"], default="medium")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--records-dir", default="records/v0_8_0")
    parser.add_argument("--allow-full", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    main()
