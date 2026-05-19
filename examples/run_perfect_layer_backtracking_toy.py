import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.evaluate import run_perfect_layer_backtracking_toy


def main():
    metrics = run_perfect_layer_backtracking_toy(
        population_per_layer=16,
        generations=120,
        top_k_candidates=3,
        seed=42,
        compile_checks_per_generation=0,
    )
    final = metrics["metrics_by_generation"][-1]
    best_target = max(row["target_ir_exact_match"] for row in metrics["metrics_by_generation"])
    print(f"dataset size: {metrics['dataset_size']}")
    print(f"layer order: {metrics['curriculum']['layer_order']}")
    print(f"generations: {metrics['generations']}")
    print(f"perfect_layer_count: {final['perfect_layer_count']}")
    print(f"freeze events: {metrics['curriculum']['freeze_events']}")
    print(f"backtracking events: {metrics['curriculum']['backtracking_events']}")
    print(f"blocked layers: {final['blocked_layers']}")
    print(f"final active_layer: {final['active_layer']}")
    print(f"final trainable_layers: {final['trainable_layers']}")
    print(f"per_layer_accuracy: {final['per_layer_accuracy']}")
    print(f"per_layer_correct_count: {final['per_layer_correct_count']}")
    print(f"per_layer_required_count: {final['per_layer_required_count']}")
    print(f"target_ir_exact_match_final: {final['target_ir_exact_match']}")
    print(f"target_ir_exact_match_best: {best_target}")
    print(f"low_score_correct_count: {final['low_score_correct_count']}")
    print(f"high_score_wrong_count: {final['high_score_wrong_count']}")
    print(f"report path: {metrics['report_path']}")


if __name__ == "__main__":
    main()
