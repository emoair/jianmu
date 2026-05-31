from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.redqueen_hydrabudget_probe import run_redqueen_hydrabudget_probe


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-v2-dir")
    parser.add_argument("--chinese-factory-dir")
    parser.add_argument("--source-records", required=True)
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--output-redqueen-dataset", required=True)
    parser.add_argument("--experiment-groups", required=True)
    parser.add_argument("--budget-thresholds", required=True)
    parser.add_argument("--budget-multipliers", required=True)
    parser.add_argument("--modes", default="quick")
    parser.add_argument("--train-samples", type=int, default=500_000)
    parser.add_argument("--eval-samples", type=int, default=50_000)
    parser.add_argument("--heldout-samples", type=int, default=50_000)
    parser.add_argument("--boundary-samples", type=int, default=50_000)
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--run-cross-process", default="true")
    parser.add_argument("--run-historical-regression", default="true")
    parser.add_argument("--progress", default="false")
    parser.add_argument("--max-runtime-hours", type=float, default=10.0)
    parser.add_argument("--checkpoint-interval-minutes", type=int, default=15)
    parser.add_argument("--seed", default="103,104,105")
    args = parser.parse_args()
    result = run_redqueen_hydrabudget_probe(
        args.source_records,
        args.output_records,
        args.output_redqueen_dataset,
        [item for item in args.experiment_groups.split(",") if item],
        [float(item) for item in args.budget_thresholds.split(",") if item],
        [float(item) for item in args.budget_multipliers.split(",") if item],
        [item for item in args.modes.split(",") if item],
        args.compile_worker_count,
        str(args.run_compiler_validation).lower() == "true",
    )
    print(json.dumps(result["readiness"], ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

