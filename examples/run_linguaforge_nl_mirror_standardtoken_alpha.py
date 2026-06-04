from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.linguaforge_nl_schema import run_all


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run v1.1-alpha LinguaForge NL-to-token alpha probe.")
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--output-dataset", required=True)
    parser.add_argument("--source-baseline-records", default="records/v1_0_1_forgeclean")
    parser.add_argument("--source-evidence-records", default="records/v0_9_28_1")
    parser.add_argument("--scales", default="pilot,medium,large")
    parser.add_argument("--target-samples", type=int, default=500000)
    parser.add_argument("--eval-samples", type=int, default=50000)
    parser.add_argument("--heldout-samples", type=int, default=50000)
    parser.add_argument("--compiler-validation-target", type=int, default=5000)
    parser.add_argument("--compiler-validation-extended-target", type=int, default=10000)
    parser.add_argument("--freeze-substrate", default="true")
    parser.add_argument("--run-substrate-lock-audit", default="true")
    parser.add_argument("--run-nl-to-standardtoken", default="true")
    parser.add_argument("--run-nl-to-mirrortoken", default="true")
    parser.add_argument("--run-token-audit", default="true")
    parser.add_argument("--run-roundtrip-eval", default="true")
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--run-paraphrase-generalization", default="true")
    parser.add_argument("--run-comfort-zone-audit", default="true")
    parser.add_argument("--run-redqueen-linguaforge-assignments", default="true")
    parser.add_argument("--run-architecture-charter-guard", default="true")
    parser.add_argument("--progress", default="false")
    parser.add_argument("--seed", default="170")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scales = [item.strip() for item in args.scales.split(",") if item.strip()]
    seed = int(str(args.seed).split(",")[0])
    if str(args.progress).lower() == "true":
        print(f"[LinguaForge] generating scales={scales} into {args.output_dataset}")
    result = run_all(
        output_dataset=args.output_dataset,
        output_records=args.output_records,
        records_root=args.records_root,
        scales=scales,
        compiler_target=args.compiler_validation_target,
        seed=seed,
    )
    if str(args.progress).lower() == "true":
        ready = result["readiness"]
        print(f"[LinguaForge] ready_for_nl_adapter_review={ready['ready_for_nl_adapter_review']}")
        print(f"[LinguaForge] recommended_claim_level={ready['recommended_claim_level']}")


if __name__ == "__main__":
    main()

