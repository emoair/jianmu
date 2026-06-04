from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.projectcartographer_schema import run_projectcartographer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run v1.0.2 ProjectCartographer substrate hardening.")
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--output-dataset", required=True)
    parser.add_argument("--source-baseline-records", default="records/v1_0_1_forgeclean")
    parser.add_argument("--source-evidence-records", default="records/v0_9_28_1")
    parser.add_argument("--scales", default="pilot,medium,large")
    parser.add_argument("--target-samples", type=int, default=1000000)
    parser.add_argument("--eval-samples", type=int, default=100000)
    parser.add_argument("--heldout-samples", type=int, default=100000)
    parser.add_argument("--syntax-frontend-target", type=int, default=200000)
    parser.add_argument("--compiler-validation-target", type=int, default=20000)
    parser.add_argument("--compiler-validation-extended-target", type=int, default=50000)
    parser.add_argument("--freeze-substrate", default="false")
    parser.add_argument("--run-project-parser", default="true")
    parser.add_argument("--run-project-to-standardtoken", default="true")
    parser.add_argument("--run-project-to-mirrortoken", default="true")
    parser.add_argument("--run-project-to-turingtoken", default="true")
    parser.add_argument("--run-token-audit", default="true")
    parser.add_argument("--run-roundtrip-eval", default="true")
    parser.add_argument("--run-symbiote-project-probe", default="true")
    parser.add_argument("--run-redqueen-project-curriculum", default="true")
    parser.add_argument("--run-comfort-zone-audit", default="true")
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--run-architecture-charter-guard", default="true")
    parser.add_argument("--progress", default="false")
    parser.add_argument("--seed", default="173")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scales = [item.strip() for item in args.scales.split(",") if item.strip()]
    seed = int(str(args.seed).split(",")[0])
    if str(args.progress).lower() == "true":
        print(f"[ProjectCartographer] generating {scales} into {args.output_dataset}")
    result = run_projectcartographer(
        output_dataset=args.output_dataset,
        output_records=args.output_records,
        scales=scales,
        syntax_target=args.syntax_frontend_target,
        compiler_target=args.compiler_validation_target,
        seed=seed,
    )
    if str(args.progress).lower() == "true":
        ready = result["project_substrate_readiness"]
        print(f"[ProjectCartographer] ready_for_substrate_hardening_review={ready['ready_for_substrate_hardening_review']}")
        print(f"[ProjectCartographer] recommended_claim_level={ready['recommended_claim_level']}")


if __name__ == "__main__":
    main()

