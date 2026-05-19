import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.branchchain.evaluate import run_branchchain_toy_experiment


def main():
    metrics = run_branchchain_toy_experiment(population_size=128, generations=30, seed=42)
    first = metrics["metrics_by_generation"][0]
    final = metrics["metrics_by_generation"][-1]
    print(f"dataset size: {metrics['dataset_size']}")
    print(f"population size: {metrics['population_size']}")
    print(f"generations: {metrics['generation_count']}")
    print(f"generation 0 mean reward: {first['mean_reward']}")
    print(f"final mean reward: {final['mean_reward']}")
    print(f"generation 0 branch_path_accuracy: {first['branch_path_accuracy']}")
    print(f"final branch_path_accuracy: {final['branch_path_accuracy']}")
    print(f"generation 0 target_ir_accuracy: {first['target_ir_accuracy']}")
    print(f"final target_ir_accuracy: {final['target_ir_accuracy']}")
    print(f"report path: {metrics['report_path']}")


if __name__ == "__main__":
    main()

