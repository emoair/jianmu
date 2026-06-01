from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.symbiote_runner import run_symbiote_probe


def main() -> None:
    parser = argparse.ArgumentParser(description="Run v0.9.23 RedQueen Symbiote freeze-thaw co-training probe.")
    parser.add_argument("--source-records-v19")
    parser.add_argument("--source-records-v20-1")
    parser.add_argument("--source-records-v21")
    parser.add_argument("--source-records-v21-1")
    parser.add_argument("--source-records-v22")
    parser.add_argument("--source-dataset-v22")
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--experiment-groups", default="")
    parser.add_argument("--modes", default="quick,medium,large")
    parser.add_argument("--train-samples", type=int, default=500000)
    parser.add_argument("--eval-samples", type=int, default=50000)
    parser.add_argument("--heldout-samples", type=int, default=50000)
    parser.add_argument("--boundary-samples", type=int, default=50000)
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--fallback-worker-count", type=int, default=8)
    parser.add_argument("--run-freeze-thaw", default="true")
    parser.add_argument("--run-comfort-zone-audit", default="true")
    parser.add_argument("--run-generalization-audit", default="true")
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--run-architecture-charter-guard", default="true")
    parser.add_argument("--progress", default="false")
    parser.add_argument("--max-runtime-hours", type=float, default=8)
    parser.add_argument("--checkpoint-interval-minutes", type=int, default=10)
    parser.add_argument("--seed", default="135,136,137,138")
    args = parser.parse_args()
    run_symbiote_probe(args.output_records, compiler_target=5000, compile_worker_count=args.compile_worker_count)


if __name__ == "__main__":
    main()
