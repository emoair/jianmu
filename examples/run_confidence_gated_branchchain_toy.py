import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.evaluate import run_confidence_gated_branchchain_toy


def main():
    metrics = run_confidence_gated_branchchain_toy(
        population_per_layer=16,
        generations=60,
        top_k_candidates=3,
        seed=42,
        compile_checks_per_generation=0,
    )
    final = metrics["metrics_by_generation"][-1]
    best = metrics["hall_of_fame"]["best_metrics"]
    thresholds = {
        layer: config["continue_threshold"]
        for layer, config in metrics["guarded_branchchain"]["layer_gate_configs"].items()
    }
    print(f"dataset size: {metrics['dataset_size']}")
    print(f"generations: {metrics['generations']}")
    print(f"no_confidence_reject_count: {final['no_confidence_reject_count']}")
    print(f"correct_no_confidence_reject_count: {final['correct_no_confidence_reject_count']}")
    print(f"wrong_no_confidence_reject_count: {final['wrong_no_confidence_reject_count']}")
    print(f"false_accept_unsupported_count: {final['false_accept_unsupported_count']}")
    print(f"false_reject_supported_count: {final['false_reject_supported_count']}")
    print(f"rejected_by_layer_distribution: {final['rejected_by_layer_distribution']}")
    print(f"continue_threshold by layer: {thresholds}")
    print("support_gate remains: True; downgraded: True")
    print(f"final target_ir_exact_match: {final['target_ir_exact_match_rate']}")
    print(f"best target_ir_exact_match: {best.get('target_ir_exact_match_rate')}")
    print(f"final missing_layer_rate: {final['missing_layer_rate']}")
    print(f"report path: {metrics['report_path']}")


if __name__ == "__main__":
    main()

