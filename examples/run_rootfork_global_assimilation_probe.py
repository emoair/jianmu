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
from jianmu.self_learning.darwinforge.global_assimilation import apply_global_assimilation, extract_assimilation_records
from jianmu.self_learning.darwinforge.metric_reconciliation import MetricScope, reconcile_metrics, summarize_global_rows
from jianmu.self_learning.darwinforge.ood_guard_balancing import apply_ood_guard_balancing
from jianmu.self_learning.darwinforge.path_diagnostics import diagnose_paths
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.darwinforge.real_scale_ladder import run_real_scale_ladder, summarize_real_scale_ladder
from jianmu.self_learning.darwinforge.root_lifecycle import RootLifecycleConfig, update_root_lifecycle
from jianmu.self_learning.darwinforge.router_score_diagnostics import find_fork_point, score_target_branch_path, summarize_router_score_diagnostics
from jianmu.self_learning.darwinforge.slot_binding_repair import apply_slot_binding_repair
from jianmu.self_learning.darwinforge.subbeam_regrowth import SubBeamConfig, SubBeamRegrowthRequest, run_prefix_conditioned_subbeam, summarize_subbeam_results
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
    global_before = _run_global_free_beam(population, eval_samples + ood, cfg, generation=0, scale_label="main_before")
    score_rows_before = _score_diagnostics(population, train, cfg)
    fork_rows = _fork_points(score_rows_before, global_before["diagnostics"])
    teacher_results, free_results = _run_subbeams(population, train, fork_rows, cfg)
    free_summary = summarize_subbeam_results(free_results, global_failed_count=len(fork_rows))
    assimilation_records = extract_assimilation_records(free_results, score_rows_before, train)
    assimilation_metrics = apply_global_assimilation(population, assimilation_records, strength=1)
    slot_metrics = apply_slot_binding_repair(population, train, score_rows_before)
    ood_balance = apply_ood_guard_balancing(population, train + ood, before_metrics=global_before["metrics"])
    global_after = _run_global_free_beam(population, eval_samples + ood, cfg, generation=1, scale_label="main_after")
    score_rows_after = _score_diagnostics(population, train, cfg)
    lifecycle = _run_lifecycle(global_after["candidates"])
    ladder_rows = run_real_scale_ladder(lambda scale: _real_scale_runner(population, eval_samples, ood, scale), skip_levels=["medium", "large"] if args.mode == "quick" else ["large"])
    ladder_summary = summarize_real_scale_ladder(
        ladder_rows,
        before_rate=global_before["metrics"]["global_correct_targetir_in_beam_rate"],
        after_rate=global_after["metrics"]["global_correct_targetir_in_beam_rate"],
    )
    reconciliation = reconcile_metrics(
        {"ood_false_accept_after": global_after["metrics"]["ood_false_accept_rate"], "ood_sample_count": len(ood)},
        ladder_rows,
    )
    before_router = summarize_router_score_diagnostics(score_rows_before)
    after_router = summarize_router_score_diagnostics(score_rows_after)
    metrics = {
        "mode": args.mode,
        "dataset_dir": str(dataset_dir),
        "train_sample_count": len(train),
        "eval_sample_count": len(eval_samples),
        "ood_sample_count": len(ood),
        "runtime_seconds": round(time.time() - started, 4),
        "path_forcing_exact_match_rate": path_forcing["path_forcing_exact_match_rate"],
        "global_correct_targetir_in_beam_rate_before": global_before["metrics"]["global_correct_targetir_in_beam_rate"],
        "global_correct_targetir_in_beam_rate_after": global_after["metrics"]["global_correct_targetir_in_beam_rate"],
        "candidate_space_failure_rate_before": global_before["metrics"]["candidate_space_failure_rate"],
        "candidate_space_failure_rate_after": global_after["metrics"]["candidate_space_failure_rate"],
        "subbeam_rescue_rate": free_summary["subbeam_rescue_rate"],
        **assimilation_metrics,
        **slot_metrics,
        "first_low_score_correct_layer_distribution_before": before_router["first_low_score_correct_layer_distribution"],
        "first_low_score_correct_layer_distribution_after": after_router["first_low_score_correct_layer_distribution"],
        **{key: value for key, value in lifecycle.items() if key not in {"events", "states"}},
        "ood_false_accept_before": global_before["metrics"]["ood_false_accept_rate"],
        "ood_false_accept_after": global_after["metrics"]["ood_false_accept_rate"],
        "arithmetic_supported_retention_rate": ood_balance["arithmetic_supported_retention_rate"],
        **reconciliation,
        **ladder_summary,
        "config": cfg,
    }
    paths = _write_outputs(
        metrics,
        Path(args.records_dir),
        assimilation_records,
        slot_metrics,
        lifecycle,
        reconciliation,
        ladder_rows,
        ood_balance,
        global_after["candidates"],
        global_after["failure_examples"],
    )
    _print_summary(metrics, paths)


def _run_global_free_beam(population, samples, cfg, generation, scale_label):
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
    candidates = []
    for sample in samples:
        features = build_training_features(sample["input_text"], canonicalization_enabled=True)
        records = []
        for genome in search.generate_paths(population, features, generation=generation):
            phenotype = synthesis.synthesize(genome, features)
            fitness = compute_fitness(genome, phenotype, sample, sandbox_optional=False)
            records.append(CandidateRecord(genome, phenotype, fitness))
        diag = diagnose_paths(sample, records, canonical_text=features.get("canonical_text")).to_dict()
        diag.update({"input_mode": sample.get("input_mode"), "structure_policy": sample.get("structure_policy"), "unsupported_reason": sample.get("unsupported_reason")})
        diagnostics.append(diag)
        for rank, record in enumerate(sorted(records, key=lambda item: item.fitness_report.total_fitness, reverse=True)[:5], start=1):
            candidates.append(_candidate_row(sample, record, rank))
    scope = MetricScope(split="eval+ood", sample_count=len(samples), evaluator_name="free_global_beam", guard_state="ood_guard_applied", population_state=scale_label, scale_label=scale_label)
    metrics = summarize_global_rows(diagnostics, scope)
    return {"metrics": metrics, "diagnostics": diagnostics, "candidates": candidates, "failure_examples": _failure_examples(diagnostics)}


def _score_diagnostics(population, samples, cfg):
    rows = []
    for sample in samples:
        if not sample.get("supported"):
            continue
        features = build_training_features(sample["input_text"], canonicalization_enabled=True)
        diag = score_target_branch_path(population, features, sample.get("target_branch_path", []), proposals_per_layer=cfg["proposals_per_layer"])
        rows.append({"sample_id": sample.get("sample_id"), "input_mode": sample.get("input_mode"), "score_diagnostic": diag})
    return rows


def _fork_points(score_rows, free_diags):
    by_id = {row["sample_id"]: row for row in free_diags}
    rows = []
    for row in score_rows:
        free = by_id.get(row["sample_id"], {})
        fork = find_fork_point(row["score_diagnostic"], free)
        rows.append({"sample_id": row["sample_id"], **fork, "score_diagnostic": row["score_diagnostic"]})
    return rows


def _run_subbeams(population, train, fork_rows, cfg):
    sample_by_id = {sample["sample_id"]: sample for sample in train}
    config = SubBeamConfig(subbeam_size=cfg["subbeam_size"], proposals_per_layer=cfg["proposals_per_layer"], exploration_quota=cfg["exploration_quota"], stochastic_samples_per_layer=cfg["stochastic_samples_per_layer"], max_complete_paths=max(cfg["subbeam_size"] * 4, 32), seed=cfg["seed"])
    teacher = []
    free = []
    for row in fork_rows[: cfg["train_limit"]]:
        sample = sample_by_id.get(row["sample_id"])
        if not sample:
            continue
        request = _request(sample, row, teacher_guided=True)
        teacher.append(run_prefix_conditioned_subbeam(population, sample, request, config))
        free.append(run_prefix_conditioned_subbeam(population, sample, _request(sample, row, teacher_guided=False), config))
    return teacher, free


def _run_lifecycle(candidate_rows):
    states = {}
    current = []
    nutrients = {}
    for row in candidate_rows[:300]:
        root_id = f"{row['sample_id']}:{row['rank']}"
        nutrient = 2.0 if row.get("target_ir_exact_match") else 0.0
        nutrients[root_id] = nutrient
        current.append({"root_id": root_id, "sample_id": row["sample_id"], "path_signature": str(row.get("decisions")), "nutrient_score": nutrient, "root_type": "high_score_wrong" if row["rank"] == 1 and not row.get("target_ir_exact_match") else "active", "stable_prefix": row.get("decisions", [])[:3]})
    return update_root_lifecycle(states, current, nutrients, RootLifecycleConfig(max_active_roots=128), generation=1)


def _real_scale_runner(population, eval_samples, ood, scale):
    cfg = {"beam_size": scale.beam_size, "proposals_per_layer": 6, "exploration_quota": 2, "stochastic_samples_per_layer": 3, "seed": 42}
    metrics = _run_global_free_beam(population, (eval_samples[: scale.eval_limit] + ood[: scale.ood_limit]), cfg, generation=scale.generations, scale_label=scale.scale_label)["metrics"]
    return {
        "evaluator_name": "free_global_beam",
        "guard_state": "ood_guard_applied",
        "population_state": "assimilated",
        "global_correct_targetir_in_beam_rate": metrics["global_correct_targetir_in_beam_rate"],
        "candidate_space_failure_rate": metrics["candidate_space_failure_rate"],
        "seeded_free_subbeam_correct_targetir_rate": 0.0,
        "subbeam_rescue_rate": 0.0,
        "ood_false_accept_rate": metrics["ood_false_accept_rate"],
        "ood_sample_count": metrics.get("unsupported_count", scale.ood_limit),
    }


def _candidate_row(sample, record, rank):
    return {"sample_id": sample.get("sample_id"), "rank": rank, "supported": sample.get("supported"), "target_ir_pred": record.phenotype.target_ir_canonical, "target_ir_exact_match": record.fitness_report.target_ir_exact_match, "fitness": record.fitness_report.total_fitness, "decisions": [[d.layer_name, d.selected] for d in record.genome.branch_path.decisions], "unsupported_pred": record.phenotype.unsupported_pred}


def _write_outputs(metrics, records_dir, assimilation_records, slot_metrics, lifecycle, reconciliation, ladder_rows, ood_balance, candidates, failures):
    records_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "metrics_path": records_dir / "rootfork_global_metrics.json",
        "report_path": records_dir / "rootfork_global_report.md",
        "global_assimilation_records_path": records_dir / "global_assimilation_records.jsonl",
        "global_assimilation_updates_path": records_dir / "global_assimilation_updates.jsonl",
        "slot_binding_repair_path": records_dir / "slot_binding_repair.json",
        "root_lifecycle_states_path": records_dir / "root_lifecycle_states.jsonl",
        "root_lifecycle_events_path": records_dir / "root_lifecycle_events.jsonl",
        "metric_reconciliation_path": records_dir / "metric_reconciliation.json",
        "real_scale_ladder_path": records_dir / "real_scale_ladder.jsonl",
        "ood_guard_reconciliation_path": records_dir / "ood_guard_reconciliation.json",
        "candidates_path": records_dir / "rootfork_global_candidates.jsonl",
        "failure_examples_path": records_dir / "rootfork_global_failure_examples.json",
    }
    paths["metrics_path"].write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    paths["report_path"].write_text(_report(metrics), encoding="utf-8")
    paths["global_assimilation_records_path"].write_text("".join(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for record in assimilation_records), encoding="utf-8")
    paths["global_assimilation_updates_path"].write_text("".join(json.dumps(update, ensure_ascii=False, sort_keys=True) + "\n" for record in assimilation_records for update in record.assimilation_updates), encoding="utf-8")
    paths["slot_binding_repair_path"].write_text(json.dumps(slot_metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    paths["root_lifecycle_states_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in lifecycle["states"]), encoding="utf-8")
    paths["root_lifecycle_events_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in lifecycle["events"]), encoding="utf-8")
    paths["metric_reconciliation_path"].write_text(json.dumps(reconciliation, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    paths["real_scale_ladder_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in ladder_rows), encoding="utf-8")
    paths["ood_guard_reconciliation_path"].write_text(json.dumps(ood_balance, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    paths["candidates_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in candidates), encoding="utf-8")
    paths["failure_examples_path"].write_text(json.dumps(failures, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


def _report(metrics):
    return "\n".join([
        "# RootFork Global Assimilation（根叉全局吸收） Report（报告）",
        "",
        "## Global Beam Before / After（全局束前后）",
        f"- global_correct_targetir_in_beam_rate_before（吸收前正确目标中间表示在束内率）: {metrics.get('global_correct_targetir_in_beam_rate_before', 0.0)}",
        f"- global_correct_targetir_in_beam_rate_after（吸收后正确目标中间表示在束内率）: {metrics.get('global_correct_targetir_in_beam_rate_after', 0.0)}",
        f"- candidate_space_failure_rate_before（吸收前候选空间失败率）: {metrics.get('candidate_space_failure_rate_before', 0.0)}",
        f"- candidate_space_failure_rate_after（吸收后候选空间失败率）: {metrics.get('candidate_space_failure_rate_after', 0.0)}",
        "",
        "## Assimilation（全局吸收）",
        f"- assimilation_record_count（吸收记录数）: {metrics.get('assimilation_record_count', 0)}",
        f"- updated_layer_distribution（更新层分布）: {metrics.get('updated_layer_distribution', {})}",
        f"- updated_option_distribution（更新选项分布）: {metrics.get('updated_option_distribution', {})}",
        "",
        "## Slot Binding Repair（槽位绑定修复）",
        f"- slot_binding_correct_rank_before / after（槽位正确排名前后）: {metrics.get('slot_binding_correct_rank_before', 0.0)} / {metrics.get('slot_binding_correct_rank_after', 0.0)}",
        f"- slot_binding_correct_score_before / after（槽位正确分数前后）: {metrics.get('slot_binding_correct_score_before', 0.0)} / {metrics.get('slot_binding_correct_score_after', 0.0)}",
        f"- first_low_score_correct_layer_distribution_before / after（首个正确低分层分布前后）: {metrics.get('first_low_score_correct_layer_distribution_before', {})} / {metrics.get('first_low_score_correct_layer_distribution_after', {})}",
        "",
        "## Root Lifecycle（根生命周期）",
        f"- active_root_count（活跃根数）: {metrics.get('active_root_count', 0)}",
        f"- starving_root_count（饥饿根数）: {metrics.get('starving_root_count', 0)}",
        f"- necrotic_archived_count（坏死归档根数）: {metrics.get('necrotic_archived_count', 0)}",
        f"- replacement_root_count（替代根数）: {metrics.get('replacement_root_count', 0)}",
        "",
        "## OOD Metric Reconciliation（分布外指标口径统一）",
        f"- ood_false_accept_before / after（分布外误接收前后）: {metrics.get('ood_false_accept_before', 0.0)} / {metrics.get('ood_false_accept_after', 0.0)}",
        f"- ood_metric_consistency_passed（分布外指标一致性通过）: {metrics.get('ood_metric_consistency_passed', False)}",
        f"- arithmetic_supported_retention_rate（算术支持保留率）: {metrics.get('arithmetic_supported_retention_rate', 0.0)}",
        "",
        "## Real Scale Ladder（真实规模阶梯）",
        f"- scale_ladder_results（规模阶梯结果）: {metrics.get('scale_ladder_results', [])}",
        f"- scale_limited_likely（可能受规模限制）: {metrics.get('scale_limited_likely', False)}",
        f"- structural_failure_likely（可能结构性失败）: {metrics.get('structural_failure_likely', False)}",
        f"- assimilation_effect_likely（可能存在吸收效果）: {metrics.get('assimilation_effect_likely', False)}",
        "",
        "## Non-Claims（非主张）",
        "- This does not prove stable DarwinForge（达尔文进化炉） convergence.",
        "- This does not prove general program synthesis.",
        "- This does not train C source text.",
        "- This does not patch old source code.",
        "- This is a RootFork Global Assimilation（根叉全局吸收） scaffold.",
    ]) + "\n"


def _request(sample, row, teacher_guided):
    return SubBeamRegrowthRequest(sample_id=sample["sample_id"], raw_text=sample["input_text"], canonical_text="", stable_prefix=row.get("stable_prefix", []), fork_layer=row.get("fork_layer"), fork_reason=row.get("fork_reason"), target_option_at_fork=row.get("correct_option_at_fork"), target_option_rank=row.get("target_option_rank"), score_gap=row.get("score_gap", 0), teacher_guided=teacher_guided)


def _failure_examples(rows):
    return {"candidate_space_failure": [row for row in rows if row.get("candidate_space_failure")][:10]}


def _ensure_dataset(dataset_dir):
    if (dataset_dir / "jianmu_v0_7_0_symbol_grounding_train.jsonl").exists():
        return dataset_dir
    quick = Path("datasets/v0_7_0_quick")
    subprocess.run([sys.executable, "-m", "jianmu.self_learning.datasets.symbol_grounding", "--size", "600", "--seed", "42", "--out", str(quick)], check=True)
    return quick


def _config(args):
    defaults = {"quick": dict(train_limit=300, eval_limit=150, ood_limit=100, generations=4, beam_size=24, subbeam_size=24, population_per_layer=24), "medium": dict(train_limit=800, eval_limit=300, ood_limit=150, generations=8, beam_size=48, subbeam_size=48, population_per_layer=32)}[args.mode]
    defaults.update({"proposals_per_layer": 6, "exploration_quota": 2, "stochastic_samples_per_layer": 3, "seed": args.seed})
    return defaults


def _print_summary(metrics, paths):
    for key in ["global_correct_targetir_in_beam_rate_before", "global_correct_targetir_in_beam_rate_after", "candidate_space_failure_rate_before", "candidate_space_failure_rate_after", "assimilation_record_count", "branch_neuron_updated_count", "ood_false_accept_before", "ood_false_accept_after"]:
        print(f"{key}: {metrics.get(key)}")
    for key, value in paths.items():
        print(f"{key}: {value}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_7_0")
    parser.add_argument("--mode", choices=["quick", "medium"], default="quick")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--records-dir", default="records/v0_7_7")
    return parser.parse_args()


if __name__ == "__main__":
    main()
