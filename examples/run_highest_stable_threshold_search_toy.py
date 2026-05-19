import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.evaluate import run_highest_stable_threshold_search_toy


def main():
    metrics = run_highest_stable_threshold_search_toy(
        population_per_layer=16,
        generations=60,
        top_k_candidates=3,
        seed=42,
        compile_checks_per_generation=0,
    )
    final = metrics["metrics_by_generation"][-1]
    best = metrics["hall_of_fame"]["best_metrics"]
    support_state = metrics["curriculum"]["threshold_controller"]["states"]["support_gate"]
    print(f"dataset size: {metrics['dataset_size']}")
    print(f"generations: {metrics['generations']}")
    print("active layer curve: " + ", ".join(row["active_layer"] for row in metrics["metrics_by_generation"]))
    print(f"freeze events: {metrics['curriculum']['freeze_events']}")
    print(f"threshold anneal events: {metrics['curriculum']['threshold_anneal_events']}")
    print(f"threshold block events: {metrics['curriculum']['threshold_block_events']}")
    print(f"frozen_threshold_by_layer: {metrics['curriculum']['frozen_threshold_by_layer']}")
    print(f"support_gate threshold history: {support_state['threshold_history']}")
    print(f"support_gate winner accuracy: {final.get('per_layer_winner_accuracy', {}).get('support_gate')}")
    print(f"support_gate recall@k: {final.get('per_layer_recall_at_k', {}).get('support_gate')}")
    print(f"support_gate confusion matrix: {final.get('support_gate_confusion_matrix')}")
    print(f"final active_layer: {final['active_layer']}")
    print(f"support_gate froze: {'support_gate' in metrics['curriculum']['frozen_threshold_by_layer']}")
    print(f"final target_ir_exact_match: {final['target_ir_exact_match_rate']}")
    print(f"best target_ir_exact_match: {best.get('target_ir_exact_match_rate')}")
    print(f"final missing_layer_rate: {final['missing_layer_rate']}")
    print(f"report path: {metrics['report_path']}")


if __name__ == "__main__":
    main()
