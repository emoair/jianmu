import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jianmu.self_learning.darwinforge.canonical_symbol_eval import (
    compare_canonical_symbol_layer,
    evaluate_canonical_symbol_layer,
    write_canonical_symbol_outputs,
)
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation


def main():
    args = parse_args()
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        quick_dir = Path("datasets/v0_7_0_quick")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "jianmu.self_learning.datasets.symbol_grounding",
                "--size",
                "600",
                "--seed",
                "42",
                "--out",
                str(quick_dir),
            ],
            check=True,
        )
        dataset_path = quick_dir / "jianmu_v0_7_0_symbol_grounding_all.jsonl"
    samples = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    sample_size = min(args.sample_size, len(samples)) if args.sample_size else len(samples)
    selected = samples[:sample_size]
    population = LayerPreservedPopulation.initialize(population_per_layer=args.population_per_layer, seed=args.seed)
    if args.canonicalization == "both":
        metrics = compare_canonical_symbol_layer(population, selected, top_k=args.top_k)
    elif args.canonicalization == "on":
        one = evaluate_canonical_symbol_layer(population, selected, top_k=args.top_k, canonicalization_enabled=True)
        metrics = {
            "without_canonicalization": one,
            "with_canonicalization": one,
            "delta": {"target_ir_exact_match": 0.0, "zh_number_expression_false_reject_rate": 0.0, "zh_number_targetir_exact_match": 0.0, "raw_vs_canonical_targetir_gap": 0.0},
            "rows_with": one["rows"],
            "rows_without": one["rows"],
        }
    else:
        one = evaluate_canonical_symbol_layer(population, selected, top_k=args.top_k, canonicalization_enabled=False)
        metrics = {
            "without_canonicalization": one,
            "with_canonicalization": one,
            "delta": {"target_ir_exact_match": 0.0, "zh_number_expression_false_reject_rate": 0.0, "zh_number_targetir_exact_match": 0.0, "raw_vs_canonical_targetir_gap": 0.0},
            "rows_with": one["rows"],
            "rows_without": one["rows"],
        }
    metrics["dataset"] = str(dataset_path)
    metrics["sample_size"] = sample_size
    paths = write_canonical_symbol_outputs(metrics, args.records_dir)
    with_canonical = metrics["with_canonicalization"]
    without = metrics["without_canonicalization"]
    print(f"dataset: {dataset_path}")
    print(f"sample size: {sample_size}")
    print(f"canonicalization_success_rate: {with_canonical['canonical_metrics']['canonicalization_success_rate']}")
    print(f"source_map_coverage: {with_canonical['canonical_metrics']['source_map_coverage']}")
    print(f"without zh_number_expression_false_reject_rate: {without['zh_number_metrics']['zh_number_expression_false_reject_rate']}")
    print(f"with zh_number_expression_false_reject_rate: {with_canonical['zh_number_metrics']['zh_number_expression_false_reject_rate']}")
    print(f"without zh_number_targetir_exact_match: {without['zh_number_metrics']['zh_number_targetir_exact_match']}")
    print(f"with zh_number_targetir_exact_match: {with_canonical['zh_number_metrics']['zh_number_targetir_exact_match']}")
    print(f"raw_vs_canonical_targetir_gap: {metrics['delta']['raw_vs_canonical_targetir_gap']}")
    print(f"ood_rejection_rate: {with_canonical['ood_metrics']['ood_rejection_rate']}")
    print(f"ood_false_accept_rate: {with_canonical['ood_metrics']['ood_false_accept_rate']}")
    print(f"metrics path: {paths['metrics_path']}")
    print(f"report path: {paths['report_path']}")
    print(f"examples path: {paths['examples_path']}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="datasets/v0_7_0/jianmu_v0_7_0_symbol_grounding_all.jsonl")
    parser.add_argument("--sample-size", type=int, default=1000)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--population-per-layer", type=int, default=32)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--canonicalization", choices=["on", "off", "both"], default="both")
    parser.add_argument("--records-dir", default="records/v0_7_1")
    return parser.parse_args()


if __name__ == "__main__":
    main()
