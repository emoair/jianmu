import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from jianmu.self_learning.prefix_dataset import build_tiny_prefix_dataset
from jianmu.self_learning.prefix_evolution import PrefixEvolutionTrainer, build_initial_population


def main():
    population_size = 64
    generations = 30
    seed = 42
    tasks = build_tiny_prefix_dataset()
    population = build_initial_population(population_size=population_size, seed=seed)
    trainer = PrefixEvolutionTrainer(
        training_tasks=tasks,
        population=population,
        generations=generations,
        seed=seed,
        top_k_retry=2,
    )
    report = trainer.train()
    generation_0 = report.task_success_by_generation[0]
    final_generation = report.task_success_by_generation[-1]
    any_compiler_success = any(value > 0 for value in report.task_success_by_generation)

    print(f"dataset size: {len(tasks)}")
    print(f"population size: {population_size}")
    print(f"generations: {generations}")
    print(f"generation 0 success rate: {generation_0:.4f}")
    print(f"final generation success rate: {final_generation:.4f}")
    print("best neurons summary:")
    for neuron in report.best_neurons[:5]:
        print(
            " - {neuron_id} {rule_type}->{target_token_type} "
            "policy={target_value_policy} score={score}".format(**neuron)
        )
    print(f"at least one compile-validated task success: {any_compiler_success}")


if __name__ == "__main__":
    main()
