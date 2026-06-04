from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.forgecorpus_algorithm_schema import run_forgecorpus


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run v1.0.3 ForgeCorpus classic C algorithm substrate.")
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--output-dataset", required=True)
    parser.add_argument("--source-baseline-records", default="records/v1_0_2_projectcartographer")
    parser.add_argument("--source-evidence-records", default="records/v0_9_28_1")
    parser.add_argument("--scales", default="pilot,medium,large")
    parser.add_argument("--target-samples", type=int, default=1000000)
    parser.add_argument("--eval-samples", type=int, default=100000)
    parser.add_argument("--heldout-samples", type=int, default=100000)
    parser.add_argument("--syntax-frontend-target", type=int, default=200000)
    parser.add_argument("--compiler-validation-target", type=int, default=20000)
    parser.add_argument("--compiler-validation-extended-target", type=int, default=50000)
    parser.add_argument("--algorithm-families", default="sorting,search,math,array,matrix,stack_queue,control,turing_witness")
    parser.add_argument("--allow-manual-dropin", default="true")
    parser.add_argument("--manual-dropin-dir", default="third_party_c_corpus")
    parser.add_argument("--require-license-audit", default="true")
    parser.add_argument("--run-classic-generator", default="true")
    parser.add_argument("--run-manual-dropin-audit", default="true")
    parser.add_argument("--run-license-audit", default="true")
    parser.add_argument("--run-algorithm-parser", default="true")
    parser.add_argument("--run-algorithm-to-projecttoken", default="true")
    parser.add_argument("--run-algorithm-to-mirrortoken", default="true")
    parser.add_argument("--run-algorithm-to-turingtoken", default="true")
    parser.add_argument("--run-token-audit", default="true")
    parser.add_argument("--run-roundtrip-eval", default="true")
    parser.add_argument("--run-heldout-variants", default="true")
    parser.add_argument("--run-redqueen-algorithm-curriculum", default="true")
    parser.add_argument("--run-symbiote-algorithm-probe", default="true")
    parser.add_argument("--run-comfort-zone-audit", default="true")
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--run-architecture-charter-guard", default="true")
    parser.add_argument("--progress", default="false")
    parser.add_argument("--seed", default="176")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scales = [s.strip() for s in args.scales.split(",") if s.strip()]
    seed = int(str(args.seed).split(",")[0])
    if str(args.progress).lower() == "true":
        print(f"[ForgeCorpus] generating {scales} into {args.output_dataset}")
    result = run_forgecorpus(
        output_dataset=args.output_dataset,
        output_records=args.output_records,
        scales=scales,
        syntax_target=args.syntax_frontend_target,
        compiler_target=args.compiler_validation_target,
        manual_dir=args.manual_dropin_dir,
        seed=seed,
    )
    if str(args.progress).lower() == "true":
        ready = result["algorithm_substrate_readiness"]
        print(f"[ForgeCorpus] ready_for_algorithm_substrate_review={ready['ready_for_algorithm_substrate_review']}")
        print(f"[ForgeCorpus] recommended_claim_level={ready['recommended_claim_level']}")


if __name__ == "__main__":
    main()

