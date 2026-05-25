from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.arithmetic_compiler_concurrency_scaling import (
    run_compiler_concurrency_scaling,
)


def _split_ints(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0.9.5.1 compiler concurrency scaling probe.")
    parser.add_argument("--records-dir", required=True)
    parser.add_argument("--fresh-records", required=True)
    parser.add_argument("--longrun-records", required=True)
    parser.add_argument("--dataset-dir", required=True)
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--worker-levels", default="4,8,16,32,64,128,256,512")
    parser.add_argument("--supported-samples", type=int, default=1000)
    parser.add_argument("--boundary-samples", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=51)
    parser.add_argument("--timeout-seconds", type=int, default=5)
    parser.add_argument("--python-worker-count", type=int, default=4)
    args = parser.parse_args()
    metrics = run_compiler_concurrency_scaling(
        records_dir=args.records_dir,
        fresh_records=args.fresh_records,
        longrun_records=args.longrun_records,
        dataset_dir=args.dataset_dir,
        output_records=args.output_records,
        worker_levels=_split_ints(args.worker_levels),
        supported_samples=args.supported_samples,
        boundary_samples=args.boundary_samples,
        seed=args.seed,
        timeout_seconds=args.timeout_seconds,
        python_worker_count=args.python_worker_count,
    )
    print(json.dumps({
        "tested_worker_levels": metrics.get("tested_worker_levels"),
        "stable_worker_levels": metrics.get("stable_worker_levels"),
        "unstable_worker_levels": metrics.get("unstable_worker_levels"),
        "best_compile_worker_count": metrics.get("best_compile_worker_count"),
        "best_samples_per_second": metrics.get("best_samples_per_second"),
        "recommended_claim_level": metrics.get("recommended_claim_level"),
        "blocking_issues": metrics.get("blocking_issues"),
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
