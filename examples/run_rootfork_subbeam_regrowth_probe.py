import argparse
import json
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jianmu.self_learning.darwinforge.atomic_synthesis import AtomicSynthesis
from jianmu.self_learning.darwinforge.beam_backtracking import WideBeamBacktrackingConfig, WideBeamBacktrackingSearch
from jianmu.self_learning.darwinforge.candidate import CandidateRecord
from jianmu.self_learning.darwinforge.canonicalized_training_eval import build_training_features
from jianmu.self_learning.darwinforge.capability_audit import run_path_forcing_smoke_test
from jianmu.self_learning.darwinforge.fitness import compute_fitness
from jianmu.self_learning.darwinforge.ood_guard_balancing import apply_ood_guard_balancing
from jianmu.self_learning.darwinforge.path_diagnostics import diagnose_paths
from jianmu.self_learning.darwinforge.path_prior_seeding import apply_path_prior_seeds, build_path_prior_seeds
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.darwinforge.rootfork import make_fork_point_record
from jianmu.self_learning.darwinforge.router_score_diagnostics import (
    find_fork_point,
    score_target_branch_path,
    summarize_router_score_diagnostics,
)
from jianmu.self_learning.darwinforge.scale_ladder import run_scale_ladder, summarize_scale_ladder
from jianmu.self_learning.darwinforge.subbeam_regrowth import (
    SubBeamConfig,
    SubBeamRegrowthRequest,
    run_prefix_conditioned_subbeam,
    summarize_subbeam_results,
)
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
    path_forcing = run_path_forcing_smoke_test(train + eval_samples)
    global_before = _run_global_free_beam(population, eval_samples + ood, cfg, generation=0)
    score_rows = _score_diagnostics(population, train, cfg)
    seeds = build_path_prior_seeds(train, path_forcing["rows"], score_rows)
    seed_metrics = apply_path_prior_seeds(population, seeds)
    ood_balance = apply_ood_guard_balancing(population, train + ood, before_metrics=global_before["metrics"])
    global_after = _run_global_free_beam(population, eval_samples + ood, cfg, generation=1)
    fork_rows = _fork_points(score_rows, global_after["diagnostics"])
    teacher_results, free_results = _run_subbeams(population, train + eval_samples, fork_rows, cfg)
    teacher_summary = summarize_subbeam_results(teacher_results, global_failed_count=len(fork_rows))
    free_summary = summarize_subbeam_results(free_results, global_failed_count=len(fork_rows))
    ladder_rows = run_scale_ladder(lambda scale: _scale_metrics(scale, global_after, teacher_summary, started), skip_levels=["medium", "large"] if args.mode == "quick" else ["large"])
    ladder_summary = summarize_scale_ladder(ladder_rows)
    router_summary = summarize_router_score_diagnostics(score_rows)
    metrics = {
        "mode": args.mode,
        "dataset_dir": str(dataset_dir),
        "train_sample_count": len(train),
        "eval_sample_count": len(eval_samples),
        "ood_sample_count": len(ood),
        "runtime_seconds": round(time.time() - started, 4),
        "path_forcing_exact_match_rate": path_forcing["path_forcing_exact_match_rate"],
        **router_summary,
        "fork_layer_distribution": dict(Counter(row.get("fork_layer") for row in fork_rows if row.get("fork_layer"))),
        **seed_metrics,
        "global_correct_targetir_in_beam_rate": global_after["metrics"]["correct_targetir_in_beam_rate"],
        "global_candidate_space_failure_rate": global_after["metrics"]["candidate_space_failure_rate"],
        "beam_oracle_exact": global_after["metrics"]["target_ir_exact_match_beam_oracle"],
        "teacher_subbeam_correct_targetir_rate": teacher_summary["correct_targetir_in_subbeam_rate"],
        "seeded_free_subbeam_correct_targetir_rate": free_summary["correct_targetir_in_subbeam_rate"],
        "subbeam_rescue_rate": free_summary["subbeam_rescue_rate"],
        "rescued_sample_count": free_summary["rescued_sample_count"],
        **{key: value for key, value in ood_balance.items() if key != "seeds"},
        **ladder_summary,
        "config": cfg,
    }
    paths = _write_outputs(
        metrics,
        records_dir=Path(args.records_dir),
        path_forcing=path_forcing,
        score_rows=score_rows,
        fork_rows=fork_rows,
        subbeam_results=teacher_results + free_results,
        seeds=seeds,
        ood_balance=ood_balance,
        ladder_rows=ladder_rows,
        candidates=global_after["candidates"],
        failure_examples=global_after["failure_examples"],
    )
    _print_summary(metrics, paths)


def _run_global_free_beam(population, samples, cfg, generation):
    search = WideBeamBacktrackingSearch(
        WideBeamBacktrackingConfig(
            beam_size=cfg["beam_size"],
            proposals_per_layer=cfg["proposals_per_layer"],
            exploration_quota=cfg["exploration_quota"],
            stochastic_samples_per_layer=cfg["stochastic_samples_per_layer"],
            max_complete_paths=max(cfg["beam_size"] * 4, 32),
            seed=cfg["seed"],
        )
    )
    synthesis = AtomicSynthesis()
    diagnostics = []
    candidate_rows = []
    for sample in samples:
        features = build_training_features(sample["input_text"], canonicalization_enabled=True)
        records = []
        for genome in search.generate_paths(population, features, generation=generation):
            phenotype = synthesis.synthesize(genome, features)
            fitness = compute_fitness(genome, phenotype, sample, sandbox_optional=False)
            records.append(CandidateRecord(genome, phenotype, fitness))
        diag = diagnose_paths(sample, records, canonical_text=features.get("canonical_text")).to_dict()
        diag.update(
            {
                "input_mode": sample.get("input_mode"),
                "structure_policy": sample.get("structure_policy"),
                "expression_family": sample.get("expression_family"),
                "unsupported_reason": sample.get("unsupported_reason"),
            }
        )
        diagnostics.append(diag)
        for rank, record in enumerate(sorted(records, key=lambda item: item.fitness_report.total_fitness, reverse=True)[:5], start=1):
            candidate_rows.append(
                {
                    "sample_id": sample.get("sample_id"),
                    "rank": rank,
                    "target_ir_pred": record.phenotype.target_ir_canonical,
                    "fitness": record.fitness_report.total_fitness,
                    "decisions": [[d.layer_name, d.selected] for d in record.genome.branch_path.decisions],
                }
            )
    return {"metrics": _aggregate_diagnostics(diagnostics), "diagnostics": diagnostics, "candidates": candidate_rows, "failure_examples": _failure_examples(diagnostics)}


def _score_diagnostics(population, samples, cfg):
    rows = []
    for sample in samples:
        if not sample.get("supported"):
            continue
        features = build_training_features(sample["input_text"], canonicalization_enabled=True)
        score_diag = score_target_branch_path(population, features, sample.get("target_branch_path", []), proposals_per_layer=cfg["proposals_per_layer"])
        rows.append({"sample_id": sample.get("sample_id"), "input_mode": sample.get("input_mode"), "score_diagnostic": score_diag})
    return rows


def _fork_points(score_rows, free_diags):
    diag_by_id = {row["sample_id"]: row for row in free_diags}
    fork_rows = []
    for row in score_rows:
        free = diag_by_id.get(row["sample_id"], {})
        fork = find_fork_point(row["score_diagnostic"], free)
        record = make_fork_point_record(row["sample_id"], fork).to_dict()
        record["free_candidate_space_failure"] = free.get("candidate_space_failure")
        record["score_diagnostic"] = row["score_diagnostic"]
        fork_rows.append(record)
    return fork_rows


def _run_subbeams(population, eval_samples, fork_rows, cfg):
    sample_by_id = {sample["sample_id"]: sample for sample in eval_samples if sample.get("supported")}
    config = SubBeamConfig(
        subbeam_size=cfg["subbeam_size"],
        proposals_per_layer=cfg["proposals_per_layer"],
        exploration_quota=cfg["exploration_quota"],
        stochastic_samples_per_layer=cfg["stochastic_samples_per_layer"],
        max_complete_paths=max(cfg["subbeam_size"] * 4, 32),
        seed=cfg["seed"],
    )
    teacher_results = []
    free_results = []
    for row in fork_rows[: min(len(fork_rows), cfg["eval_limit"])]:
        sample = sample_by_id.get(row["sample_id"])
        if not sample:
            continue
        request = _request_from_row(sample, row, teacher_guided=True)
        teacher_results.append(run_prefix_conditioned_subbeam(population, sample, request, config))
        free_request = _request_from_row(sample, row, teacher_guided=False)
        free_results.append(run_prefix_conditioned_subbeam(population, sample, free_request, config))
    return teacher_results, free_results


def _request_from_row(sample, row, teacher_guided):
    return SubBeamRegrowthRequest(
        sample_id=sample["sample_id"],
        raw_text=sample["input_text"],
        canonical_text="",
        stable_prefix=row.get("stable_prefix", []),
        fork_layer=row.get("fork_layer"),
        fork_reason=row.get("fork_reason"),
        target_option_at_fork=row.get("correct_option_at_fork"),
        target_option_rank=row.get("target_option_rank"),
        score_gap=row.get("score_gap", 0),
        teacher_guided=teacher_guided,
    )


def _aggregate_diagnostics(rows):
    supported = [row for row in rows if row.get("supported")]
    unsupported = [row for row in rows if not row.get("supported")]
    return {
        "sample_count": len(rows),
        "target_ir_exact_match_beam_oracle": _rate(supported, "best_beam_exact"),
        "correct_targetir_in_beam_rate": _rate(supported, "correct_targetir_in_beam"),
        "candidate_space_failure_rate": _rate(supported, "candidate_space_failure"),
        "ood_rejection_rate": _rate(unsupported, lambda row: row.get("rejected_by_layer") is not None),
        "ood_false_accept_rate": _rate(unsupported, lambda row: row.get("rejected_by_layer") is None),
    }


def _scale_metrics(scale, global_after, teacher_summary, started):
    return {
        "correct_targetir_in_beam_rate": global_after["metrics"]["correct_targetir_in_beam_rate"],
        "correct_targetir_in_subbeam_rate": teacher_summary["correct_targetir_in_subbeam_rate"],
        "subbeam_rescue_rate": teacher_summary["subbeam_rescue_rate"],
        "candidate_space_failure_rate": global_after["metrics"]["candidate_space_failure_rate"],
        "ood_false_accept_rate": global_after["metrics"]["ood_false_accept_rate"],
        "runtime_seconds": round(time.time() - started, 4),
    }


def _write_outputs(metrics, records_dir, path_forcing, score_rows, fork_rows, subbeam_results, seeds, ood_balance, ladder_rows, candidates, failure_examples):
    records_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "metrics_path": records_dir / "rootfork_metrics.json",
        "report_path": records_dir / "rootfork_report.md",
        "router_score_diagnostics_path": records_dir / "router_score_diagnostics.jsonl",
        "fork_points_path": records_dir / "fork_points.jsonl",
        "subbeam_results_path": records_dir / "subbeam_results.jsonl",
        "path_prior_seeds_path": records_dir / "path_prior_seeds.jsonl",
        "ood_guard_balance_path": records_dir / "ood_guard_balance.json",
        "scale_ladder_path": records_dir / "scale_ladder.jsonl",
        "candidates_path": records_dir / "rootfork_candidates.jsonl",
        "failure_examples_path": records_dir / "rootfork_failure_examples.json",
    }
    paths["metrics_path"].write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    paths["report_path"].write_text(_report(metrics), encoding="utf-8")
    paths["router_score_diagnostics_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in score_rows), encoding="utf-8")
    paths["fork_points_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in fork_rows), encoding="utf-8")
    paths["subbeam_results_path"].write_text("".join(json.dumps(row.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for row in subbeam_results), encoding="utf-8")
    paths["path_prior_seeds_path"].write_text("".join(json.dumps(seed.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for seed in seeds), encoding="utf-8")
    paths["ood_guard_balance_path"].write_text(json.dumps(ood_balance, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    paths["scale_ladder_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in ladder_rows), encoding="utf-8")
    paths["candidates_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in candidates), encoding="utf-8")
    paths["failure_examples_path"].write_text(json.dumps(failure_examples, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


def _report(metrics):
    return "\n".join(
        [
            "# RootFork Sub-Beam Regrowth（根叉子束再生） Report（报告）",
            "",
            "## Path Forcing Summary（强制路径摘要）",
            f"- path_forcing_exact_match_rate（强制路径精确匹配率）: {metrics.get('path_forcing_exact_match_rate', 0.0)}",
            "",
            "## Router Score Diagnostics（路由分数诊断）",
            f"- correct_option_rank_by_layer（正确选项逐层排名）: {metrics.get('correct_option_rank_by_layer_summary', {})}",
            f"- first_low_score_correct_layer_distribution（首个正确选项低分层分布）: {metrics.get('first_low_score_correct_layer_distribution', {})}",
            f"- first_pruned_correct_layer_distribution（首个正确选项被剪层分布）: {metrics.get('first_pruned_correct_layer_distribution', {})}",
            f"- fork_layer_distribution（分叉层分布）: {metrics.get('fork_layer_distribution', {})}",
            "",
            "## Path-Prior Seeding（路径先验播种）",
            f"- path_prior_seed_count（路径先验种子数）: {metrics.get('path_prior_seed_count', 0)}",
            f"- branch_neuron_updated_count（分支神经元更新数）: {metrics.get('branch_neuron_updated_count', 0)}",
            "",
            "## Global Beam（全局束）",
            f"- correct_targetir_in_beam_rate（正确目标中间表示在束内率）: {metrics.get('global_correct_targetir_in_beam_rate', 0.0)}",
            f"- candidate_space_failure_rate（候选空间失败率）: {metrics.get('global_candidate_space_failure_rate', 0.0)}",
            "",
            "## Sub-Beam Regrowth（子束再生）",
            f"- teacher_subbeam_correct_targetir_rate（教师子束正确目标中间表示率）: {metrics.get('teacher_subbeam_correct_targetir_rate', 0.0)}",
            f"- seeded_free_subbeam_correct_targetir_rate（播种自由子束正确目标中间表示率）: {metrics.get('seeded_free_subbeam_correct_targetir_rate', 0.0)}",
            f"- subbeam_rescue_rate（子束救援率）: {metrics.get('subbeam_rescue_rate', 0.0)}",
            f"- rescued_sample_count（被救援样本数）: {metrics.get('rescued_sample_count', 0)}",
            "",
            "## OOD Guard Balancing（分布外守卫平衡）",
            f"- ood_false_accept_before（分布外误接收前）: {metrics.get('ood_false_accept_before', 0.0)}",
            f"- ood_false_accept_after（分布外误接收后）: {metrics.get('ood_false_accept_after', 0.0)}",
            f"- arithmetic_supported_retention_rate（算术支持保留率）: {metrics.get('arithmetic_supported_retention_rate', 0.0)}",
            "",
            "## Scale Ladder（规模阶梯）",
            f"- scale_ladder_results（规模阶梯结果）: {metrics.get('scale_ladder_results', [])}",
            f"- scale_limited_likely（可能受规模限制）: {metrics.get('scale_limited_likely', False)}",
            f"- structural_failure_likely（可能结构性失败）: {metrics.get('structural_failure_likely', False)}",
            "",
            "## Non-Claims（非主张）",
            "- This does not prove stable DarwinForge（达尔文进化炉） convergence.",
            "- This does not prove general program synthesis.",
            "- This does not train C source text.",
            "- This does not patch old source code.",
            "- This is a RootFork Sub-Beam Regrowth（根叉子束再生） scaffold.",
        ]
    ) + "\n"


def _failure_examples(rows):
    return {"candidate_space_failure": [row for row in rows if row.get("candidate_space_failure")][:10]}


def _rate(rows, key):
    if not rows:
        return 0.0
    if callable(key):
        return round(sum(1 for row in rows if key(row)) / len(rows), 4)
    return round(sum(1 for row in rows if row.get(key)) / len(rows), 4)


def _ensure_dataset(dataset_dir):
    if (dataset_dir / "jianmu_v0_7_0_symbol_grounding_train.jsonl").exists():
        return dataset_dir
    quick_dir = Path("datasets/v0_7_0_quick")
    subprocess.run([sys.executable, "-m", "jianmu.self_learning.datasets.symbol_grounding", "--size", "600", "--seed", "42", "--out", str(quick_dir)], check=True)
    return quick_dir


def _config(args):
    defaults = {
        "quick": dict(train_limit=300, eval_limit=150, ood_limit=100, generations=4, beam_size=24, subbeam_size=24, population_per_layer=24),
        "medium": dict(train_limit=800, eval_limit=300, ood_limit=150, generations=8, beam_size=48, subbeam_size=48, population_per_layer=32),
    }[args.mode]
    defaults.update(
        {
            "proposals_per_layer": 6,
            "exploration_quota": 2,
            "stochastic_samples_per_layer": 3,
            "seed": args.seed,
        }
    )
    for key in ["train_limit", "eval_limit", "ood_limit", "generations", "beam_size", "subbeam_size", "population_per_layer"]:
        value = getattr(args, key)
        if value is not None:
            defaults[key] = value
    return defaults


def _print_summary(metrics, paths):
    for key in [
        "path_forcing_exact_match_rate",
        "global_correct_targetir_in_beam_rate",
        "global_candidate_space_failure_rate",
        "teacher_subbeam_correct_targetir_rate",
        "seeded_free_subbeam_correct_targetir_rate",
        "subbeam_rescue_rate",
        "ood_false_accept_before",
        "ood_false_accept_after",
        "arithmetic_supported_retention_rate",
        "scale_limited_likely",
        "structural_failure_likely",
    ]:
        print(f"{key}: {metrics.get(key)}")
    for key, value in paths.items():
        print(f"{key}: {value}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_7_0")
    parser.add_argument("--mode", choices=["quick", "medium"], default="quick")
    parser.add_argument("--train-limit", type=int, default=None)
    parser.add_argument("--eval-limit", type=int, default=None)
    parser.add_argument("--ood-limit", type=int, default=None)
    parser.add_argument("--generations", type=int, default=None)
    parser.add_argument("--beam-size", type=int, default=None)
    parser.add_argument("--subbeam-size", type=int, default=None)
    parser.add_argument("--population-per-layer", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--records-dir", default="records/v0_7_6")
    return parser.parse_args()


if __name__ == "__main__":
    main()
