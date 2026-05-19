import json
from pathlib import Path

from jianmu.self_learning.darwinforge.evolution import DarwinForgeTrainer


RECORD_DIR = Path("records/v0_6")
METRICS_PATH = RECORD_DIR / "darwinforge_toy_metrics.json"
REPORT_PATH = RECORD_DIR / "darwinforge_toy_report.md"
CANDIDATES_PATH = RECORD_DIR / "darwinforge_toy_candidates.jsonl"
HARD_CASES_PATH = RECORD_DIR / "darwinforge_hard_cases.jsonl"


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
