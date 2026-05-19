import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.evaluate import run_architecture_aligned_dataset_toy


def main():
    metrics = run_architecture_aligned_dataset_toy(
        population_per_layer=16,
        generations=60,
        top_k_candidates=3,
        seed=42,
        compile_checks_per_generation=0,
    )
    summary = metrics["dataset_summary"]
    comparison = metrics["comparison"]
    new_final = metrics["new_metrics"]["metrics_by_generation"][-1]
    best = metrics["new_metrics"]["hall_of_fame"]["best_metrics"]
    print(f"dataset size: {summary['dataset_size']}")
    print(f"supported count: {summary['supported_count']}")
    print(f"ood count: {summary['ood_count']}")
    print(f"input_mode counts: {summary['input_mode_counts']}")
    print(f"paraphrase_group counts: {summary['paraphrase_group_counts']}")
    print(f"old toy target_ir_exact_match: {comparison['old_target_ir_exact_match']}")
    print(f"architecture-aligned target_ir_exact_match: {comparison['new_target_ir_exact_match']}")
    print(f"old false_reject_supported_count: {comparison['old_false_reject_supported_count']}")
    print(f"new false_reject_supported_count: {comparison['new_false_reject_supported_count']}")
    print(f"old language_target reject count: {comparison['old_language_target_reject_count']}")
    print(f"new language_target reject count: {comparison['new_language_target_reject_count']}")
    print(f"no_confidence_reject_count: {new_final['no_confidence_reject_count']}")
    print(f"correct_no_confidence_reject_count: {new_final['correct_no_confidence_reject_count']}")
    print(f"wrong_no_confidence_reject_count: {new_final['wrong_no_confidence_reject_count']}")
    print(f"false_accept_unsupported_count: {new_final['false_accept_unsupported_count']}")
    print(f"false_reject_supported_count: {new_final['false_reject_supported_count']}")
    print(f"language_target reject count: {new_final.get('rejected_by_layer_distribution', {}).get('language_target', 0)}")
    print(f"true_missing_layer_rate: {new_final['true_missing_layer_rate']}")
    print(f"early_reject_short_path_rate: {new_final['early_reject_short_path_rate']}")
    print(f"final target_ir_exact_match: {new_final['target_ir_exact_match_rate']}")
    print(f"best target_ir_exact_match: {best['target_ir_exact_match_rate']}")
    print(f"final missing_layer_rate: {new_final['missing_layer_rate']}")
    print(f"OOD english rejection behavior: {metrics['ood_english_rejection_behavior']}")
    print(f"report path: {metrics['report_path']}")


if __name__ == "__main__":
    main()
