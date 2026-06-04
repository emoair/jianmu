from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.algorithm_variant_core import run_variant_scale_probe


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run v1.0.3.1 ForgeCorpus algorithm variant scale probe.")
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--source-records-v1-0-3", required=True)
    parser.add_argument("--source-dataset-v1-0-3", required=True)
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--output-dataset", required=True)
    parser.add_argument("--scales", default="pilot,medium,large")
    parser.add_argument("--target-samples", type=int, default=2_000_000)
    parser.add_argument("--eval-samples", type=int, default=200_000)
    parser.add_argument("--heldout-samples", type=int, default=200_000)
    parser.add_argument("--syntax-frontend-target", type=int, default=300_000)
    parser.add_argument("--compiler-validation-target", type=int, default=20_000)
    parser.add_argument("--compiler-validation-extended-target", type=int, default=50_000)
    parser.add_argument("--algorithm-families", default="sorting,search,math,array,matrix,stack_queue,control,turing_witness")
    parser.add_argument("--variant-policies", default="variable_renaming,function_renaming,constant_mutation,array_size,loop_direction,boundary_value,sorting_order,helper_split,recursion_base_case,matrix_dimension,stack_queue_capacity")
    parser.add_argument("--run-metric-freshness-audit", default="true")
    parser.add_argument("--run-sample-accounting", default="true")
    parser.add_argument("--run-semantic-skeleton-builder", default="true")
    parser.add_argument("--run-requirement-spec-builder", default="true")
    parser.add_argument("--run-variant-generator", default="true")
    parser.add_argument("--run-variant-tokenizer", default="true")
    parser.add_argument("--run-token-audit", default="true")
    parser.add_argument("--run-roundtrip-eval", default="true")
    parser.add_argument("--run-heldout-variant-eval", default="true")
    parser.add_argument("--run-heldout-failure-taxonomy", default="true")
    parser.add_argument("--run-redqueen-variant-curriculum", default="true")
    parser.add_argument("--run-symbiote-variant-probe", default="true")
    parser.add_argument("--run-comfort-zone-audit", default="true")
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--run-architecture-charter-guard", default="true")
    parser.add_argument("--progress", default="false")
    parser.add_argument("--seed", default="179")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scales = [s.strip() for s in args.scales.split(",") if s.strip()]
    seed = int(str(args.seed).split(",")[0])
    if str(args.progress).lower() == "true":
        print(f"[ForgeCorpusVariant] generating {scales} into {args.output_dataset}")
    result = run_variant_scale_probe(
        output_dataset=args.output_dataset,
        output_records=args.output_records,
        source_records_v1_0_3=args.source_records_v1_0_3,
        source_dataset_v1_0_3=args.source_dataset_v1_0_3,
        scales=scales,
        syntax_target=args.syntax_frontend_target,
        compiler_target=args.compiler_validation_target,
        seed=seed,
    )
    if str(args.progress).lower() == "true":
        ready = result["variant_substrate_readiness"]
        print(f"[ForgeCorpusVariant] ready_for_algorithm_variant_review={ready['ready_for_algorithm_variant_review']}")
        print(f"[ForgeCorpusVariant] recommended_claim_level={ready['recommended_claim_level']}")


if __name__ == "__main__":
    main()
