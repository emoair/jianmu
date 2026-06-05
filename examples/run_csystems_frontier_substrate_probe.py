from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.csystems_frontier_core import run_csystems_probe


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run v1.0.4 CSystems frontier substrate probe.")
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--source-records-v1-0-3-1", required=True)
    parser.add_argument("--source-dataset-v1-0-3-1", required=True)
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--output-dataset", required=True)
    parser.add_argument("--scale", default="full")
    parser.add_argument("--target-samples", type=int, default=5_000_000)
    parser.add_argument("--syntax-frontend-target", type=int, default=600_000)
    parser.add_argument("--compiler-validation-target", type=int, default=50_000)
    parser.add_argument("--max-runtime-hours", type=float, default=6)
    parser.add_argument("--hard-stop-hours", type=float, default=6.5)
    parser.add_argument("--feature-families", default="pointer,malloc,fileio,multifile,struct,mixed_system_algorithm")
    parser.add_argument("--run-pointer-frontier", default="true")
    parser.add_argument("--run-malloc-frontier", default="true")
    parser.add_argument("--run-fileio-frontier", default="true")
    parser.add_argument("--run-multifile-frontier", default="true")
    parser.add_argument("--run-struct-frontier", default="true")
    parser.add_argument("--run-mixed-system-algorithm", default="true")
    parser.add_argument("--run-token-audit", default="true")
    parser.add_argument("--run-memory-contract-audit", default="true")
    parser.add_argument("--run-fileio-sandbox-audit", default="true")
    parser.add_argument("--run-multifile-build-validation", default="true")
    parser.add_argument("--run-roundtrip-eval", default="true")
    parser.add_argument("--run-heldout-eval", default="true")
    parser.add_argument("--run-failure-taxonomy", default="true")
    parser.add_argument("--run-redqueen-csystems-curriculum", default="true")
    parser.add_argument("--run-comfort-zone-audit", default="true")
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--run-architecture-charter-guard", default="true")
    parser.add_argument("--progress", default="false")
    parser.add_argument("--seed", default="182")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    seed = int(str(args.seed).split(",")[0])
    if str(args.progress).lower() == "true":
        print(f"[CSystems] running {args.scale} into {args.output_dataset}")
    result = run_csystems_probe(
        output_dataset=args.output_dataset,
        output_records=args.output_records,
        scale=args.scale,
        syntax_target=args.syntax_frontend_target,
        compiler_target=args.compiler_validation_target,
        max_runtime_hours=args.max_runtime_hours,
        hard_stop_hours=args.hard_stop_hours,
        seed=seed,
    )
    if str(args.progress).lower() == "true":
        ready = result["csystems_readiness"]
        print(f"[CSystems] full_scale_completed={ready['full_scale_completed']}")
        print(f"[CSystems] recommended_claim_level={ready['recommended_claim_level']}")


if __name__ == "__main__":
    main()
