from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.linguaforge_nl_alpha_core import run_linguaforge_alpha


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run v1.1.1 LinguaForge NL-to-ProjectToken CSystems Alpha.")
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--source-records-v1-0-4-1", required=True)
    parser.add_argument("--source-dataset-v1-0-4-1", required=True)
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--output-dataset", required=True)
    parser.add_argument("--scale", default="full")
    parser.add_argument("--target-samples", type=int, default=5_000_000)
    parser.add_argument("--eval-samples", type=int, default=300_000)
    parser.add_argument("--heldout-samples", type=int, default=300_000)
    parser.add_argument("--compiler-validation-target", type=int, default=20_000)
    parser.add_argument("--compiler-validation-extended-target", type=int, default=50_000)
    parser.add_argument("--wall-clock-min-hours", type=float, default=6.0)
    parser.add_argument("--max-runtime-hours", type=float, default=6.0)
    parser.add_argument("--hard-stop-hours", type=float, default=6.5)
    parser.add_argument("--nl-families", default="")
    parser.add_argument("--naturalness-levels", default="")
    parser.add_argument("--run-substrate-lock-audit", default="true")
    parser.add_argument("--run-token-to-nl-teacher", default="true")
    parser.add_argument("--run-nl-dataset-builder", default="true")
    parser.add_argument("--run-nl-paraphrase-builder", default="true")
    parser.add_argument("--run-nl-contrastive-pairs", default="true")
    parser.add_argument("--run-nl-requirement-parser", default="true")
    parser.add_argument("--run-nl-to-projecttoken", default="true")
    parser.add_argument("--run-nl-to-algorithmtoken", default="true")
    parser.add_argument("--run-nl-to-csystemstoken", default="true")
    parser.add_argument("--run-nl-to-symbolbindingtoken", default="true")
    parser.add_argument("--run-token-audit", default="true")
    parser.add_argument("--run-bidirectional-alignment", default="true")
    parser.add_argument("--run-roundtrip-eval", default="true")
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--run-heldout-natural-nl", default="true")
    parser.add_argument("--run-failure-taxonomy", default="true")
    parser.add_argument("--run-redqueen-wide-nl-curriculum", default="true")
    parser.add_argument("--run-comfort-zone-audit", default="true")
    parser.add_argument("--run-architecture-charter-guard", default="true")
    parser.add_argument("--progress", default="false")
    parser.add_argument("--seed", default="188")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    seed = int(str(args.seed).split(",")[0])
    if str(args.progress).lower() == "true":
        print(f"[LinguaForge] running {args.scale} into {args.output_dataset}")
    result = run_linguaforge_alpha(
        output_dataset=args.output_dataset,
        output_records=args.output_records,
        source_records_v1_0_4_1=args.source_records_v1_0_4_1,
        scale=args.scale,
        target_samples=args.target_samples,
        eval_samples=args.eval_samples,
        heldout_samples=args.heldout_samples,
        compiler_validation_target=args.compiler_validation_target,
        compiler_validation_extended_target=args.compiler_validation_extended_target,
        wall_clock_min_hours=args.wall_clock_min_hours,
        max_runtime_hours=args.max_runtime_hours,
        hard_stop_hours=args.hard_stop_hours,
        seed=seed,
    )
    if str(args.progress).lower() == "true":
        ready = result["linguaforge_nl_readiness"]
        print(f"[LinguaForge] full_scale_completed={ready['full_scale_completed']}")
        print(f"[LinguaForge] wall_clock_hours={ready['wall_clock_hours']}")
        print(f"[LinguaForge] recommended_claim_level={ready['recommended_claim_level']}")


if __name__ == "__main__":
    main()
