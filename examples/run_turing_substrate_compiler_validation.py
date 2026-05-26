from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.turing_substrate_compiler_validation import run_turing_substrate_compiler_validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_9_6_turing_substrate_curriculum")
    parser.add_argument("--output-records", default="records/v0_9_6")
    parser.add_argument("--scales", default="small,medium,large")
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--supported-samples", type=int, default=5000)
    parser.add_argument("--boundary-samples", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=52)
    parser.add_argument("--timeout-seconds", type=int, default=5)
    args = parser.parse_args()
    result = run_turing_substrate_compiler_validation(
        args.dataset_dir,
        args.output_records,
        [part.strip() for part in args.scales.split(",") if part.strip()],
        args.compile_worker_count,
        args.supported_samples,
        args.boundary_samples,
        args.seed,
        args.timeout_seconds,
    )
    print(json.dumps({
        "compile_worker_count": result["compile_worker_count"],
        "backend_type": result["backend_type"],
        "real_compiler_invocation_count": result["real_compiler_invocation_count"],
        "compiler_verified_correct_rate": result["compiler_verified_correct_rate"],
        "boundary_compiler_misroute_count": result["boundary_compiler_misroute_count"],
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
