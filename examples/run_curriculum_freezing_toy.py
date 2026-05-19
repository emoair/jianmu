import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.evaluate import run_curriculum_freezing_toy


def main():
    metrics = run_curriculum_freezing_toy(
        population_per_layer=16,
        generations=40,
        top_k_candidates=3,
        seed=42,
        compile_checks_per_generation=4,
    )
    first = metrics["metrics_by_generation"][0]
    final = metrics["metrics_by_generation"][-1]
    best = metrics["hall_of_fame"]["best_metrics"]
    print(f"dataset size: {metrics['dataset_size']}")
    print(f"generations: {metrics['generations']}")
    print(f"layer order: {', '.join(metrics['curriculum']['layer_order'])}")
    print(f"freeze events: {metrics['curriculum']['freeze_events']}")
    print(f"unfreeze events: {metrics['curriculum']['unfreeze_events']}")
    print(f"generation 0 mean fitness: {first['mean_fitness']}")
    print(f"final mean fitness: {final['mean_fitness']}")
    print(f"best mean fitness: {best.get('mean_fitness')}")
    print(f"generation 0 target_ir_exact_match: {first['target_ir_exact_match_rate']}")
    print(f"final target_ir_exact_match: {final['target_ir_exact_match_rate']}")
    print(f"best target_ir_exact_match: {best.get('target_ir_exact_match_rate')}")
    print(f"generation 0 missing_layer_rate: {first['missing_layer_rate']}")
    print(f"final missing_layer_rate: {final['missing_layer_rate']}")
    print(f"best generation: {metrics['hall_of_fame']['best_generation']}")
    print(f"report path: {metrics['report_path']}")


if __name__ == "__main__":
    main()

