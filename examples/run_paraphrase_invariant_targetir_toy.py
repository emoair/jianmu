import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.evaluate import run_paraphrase_invariant_targetir_toy


def main():
    metrics = run_paraphrase_invariant_targetir_toy(
        population_per_layer=16,
        generations=80,
        top_k_candidates=3,
        seed=42,
        compile_checks_per_generation=0,
    )
    first = metrics["metrics_by_generation"][0]
    final = metrics["metrics_by_generation"][-1]
    best = metrics["best_metrics"]
    print(f"dataset size: {metrics['dataset_size']}")
    print(f"supported group count: {metrics['supported_paraphrase_group_count']}")
    print(f"OOD count: {metrics['ood_count']}")
    print(f"generation 0 sample_target_ir_exact_match: {first['sample_target_ir_exact_match']}")
    print(f"final sample_target_ir_exact_match: {final['sample_target_ir_exact_match']}")
    print(f"best sample_target_ir_exact_match: {best['sample_target_ir_exact_match']}")
    print(f"generation 0 group_targetir_consistency: {first['group_targetir_consistency']}")
    print(f"final group_targetir_consistency: {final['group_targetir_consistency']}")
    print(f"best group_targetir_consistency: {best['group_targetir_consistency']}")
    print(f"generation 0 group_targetir_exact_match: {first['group_targetir_exact_match']}")
    print(f"final group_targetir_exact_match: {final['group_targetir_exact_match']}")
    print(f"best group_targetir_exact_match: {best['group_targetir_exact_match']}")
    print(f"cross_mode_consistency: {final['cross_mode_consistency']}")
    print(f"paraphrase_collapse_rate: {final['paraphrase_collapse_rate']}")
    print(f"ood_rejection_rate: {final['ood_rejection_rate']}")
    print(f"ood_false_accept_rate: {final['ood_false_accept_rate']}")
    print(f"report path: {metrics['report_path']}")


if __name__ == "__main__":
    main()
