import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.evaluate import run_darwinforge_toy


def main():
    metrics = run_darwinforge_toy(
        population_per_layer=16,
        generations=30,
        top_k_candidates=3,
        seed=42,
        compile_checks_per_generation=8,
    )
    first = metrics["metrics_by_generation"][0]
    final = metrics["metrics_by_generation"][-1]
    print(f"dataset size: {metrics['dataset_size']}")
    print(f"generations: {metrics['generations']}")
    print(f"population_per_layer: {metrics['population_per_layer']}")
    print(f"generation 0 mean fitness: {first['mean_fitness']}")
    print(f"final mean fitness: {final['mean_fitness']}")
    print(f"generation 0 target_ir_exact_match: {first['target_ir_exact_match_rate']}")
    print(f"final target_ir_exact_match: {final['target_ir_exact_match_rate']}")
    print(f"generation 0 missing_layer_rate: {first['missing_layer_rate']}")
    print(f"final missing_layer_rate: {final['missing_layer_rate']}")
    print(f"hard_case_count: {metrics['hard_case_count']}")
    print(f"report path: {metrics['report_path']}")


if __name__ == "__main__":
    main()
