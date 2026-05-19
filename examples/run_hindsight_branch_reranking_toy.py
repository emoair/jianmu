import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.evaluate import run_hindsight_branch_reranking_toy


def main():
    metrics = run_hindsight_branch_reranking_toy(
        population_per_layer=16,
        generations=80,
        top_k_candidates=3,
        beam_width=5,
        seed=42,
        compile_checks_per_generation=0,
    )
    first = metrics["metrics_by_generation"][0]
    final = metrics["metrics_by_generation"][-1]
    print(f"dataset size: {metrics['dataset_size']}")
    print(f"supported group count: {metrics['supported_group_count']}")
    print(f"OOD count: {metrics['ood_count']}")
    print(f"generation 0 single_winner_sample_exact_match: {first['single_winner_sample_exact_match']}")
    print(f"final single_winner_sample_exact_match: {final['single_winner_sample_exact_match']}")
    print(f"final reranked_sample_exact_match: {final['reranked_sample_exact_match']}")
    print(f"final group_beam_exact_match: {final['group_beam_exact_match']}")
    print(f"low_score_correct_count: {final['low_score_correct_count']}")
    print(f"high_score_wrong_count: {final['high_score_wrong_count']}")
    print(f"rerank_improvement_count: {final['rerank_improvement_count']}")
    print(f"rerank_regression_count: {final['rerank_regression_count']}")
    print(f"wrong_consistent_group_count: {final['wrong_consistent_group_count']}")
    print(f"pruning_candidate_count: {final['pruning_candidate_count']}")
    print(f"collapse_penalty_hits: {final['collapse_penalty_hits']}")
    print(f"ood_rejection_rate: {final['ood_rejection_rate']}")
    print(f"ood_false_accept_rate: {final['ood_false_accept_rate']}")
    print(f"report path: {metrics['report_path']}")
    print(f"pruning candidates path: {metrics['pruning_candidates_path']}")


if __name__ == "__main__":
    main()
