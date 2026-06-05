from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.symbol_binding_longhaul_core import run_symbol_binding_longhaul


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run v1.0.4.1 RedQueen symbol binding longhaul.")
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--source-records-v1-0-4", required=True)
    parser.add_argument("--source-dataset-v1-0-4", required=True)
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--output-dataset", required=True)
    parser.add_argument("--scale", default="full")
    parser.add_argument("--target-samples", type=int, default=5_000_000)
    parser.add_argument("--syntax-frontend-target", type=int, default=600_000)
    parser.add_argument("--compiler-validation-target", type=int, default=50_000)
    parser.add_argument("--compiler-validation-extended-target", type=int, default=100_000)
    parser.add_argument("--wall-clock-min-hours", type=float, default=6)
    parser.add_argument("--max-runtime-hours", type=float, default=6)
    parser.add_argument("--hard-stop-hours", type=float, default=6.5)
    parser.add_argument("--binding-families", default="identifier,scope,pointer,malloc,fileio,struct,multifile,string_comment_guard")
    parser.add_argument("--run-symbol-table-builder", default="true")
    parser.add_argument("--run-symbol-guided-renamer", default="true")
    parser.add_argument("--run-regex-surface-perturbation", default="true")
    parser.add_argument("--run-regex-guard", default="true")
    parser.add_argument("--run-symbol-mutation-generator", default="true")
    parser.add_argument("--run-tokenizer", default="true")
    parser.add_argument("--run-token-audit", default="true")
    parser.add_argument("--run-roundtrip-eval", default="true")
    parser.add_argument("--run-equivalence-validation", default="true")
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--run-real-compiler-accounting-audit", default="true")
    parser.add_argument("--run-heldout-symbol-binding", default="true")
    parser.add_argument("--run-failure-taxonomy", default="true")
    parser.add_argument("--run-redqueen-symbol-binding-curriculum", default="true")
    parser.add_argument("--run-comfort-zone-audit", default="true")
    parser.add_argument("--run-architecture-charter-guard", default="true")
    parser.add_argument("--progress", default="false")
    parser.add_argument("--seed", default="185")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    seed = int(str(args.seed).split(",")[0])
    if str(args.progress).lower() == "true":
        print(f"[SymbolBinding] running {args.scale} into {args.output_dataset}")
    result = run_symbol_binding_longhaul(
        output_dataset=args.output_dataset,
        output_records=args.output_records,
        scale=args.scale,
        syntax_target=args.syntax_frontend_target,
        compiler_target=args.compiler_validation_target,
        extended_target=args.compiler_validation_extended_target,
        wall_clock_min_hours=args.wall_clock_min_hours,
        max_runtime_hours=args.max_runtime_hours,
        hard_stop_hours=args.hard_stop_hours,
        seed=seed,
    )
    if str(args.progress).lower() == "true":
        ready = result["symbol_binding_readiness"]
        print(f"[SymbolBinding] full_scale_completed={ready['full_scale_completed']}")
        print(f"[SymbolBinding] wall_clock_hours={ready['wall_clock_hours']}")
        print(f"[SymbolBinding] recommended_claim_level={ready['recommended_claim_level']}")


if __name__ == "__main__":
    main()

