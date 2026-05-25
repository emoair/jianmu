from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.arithmetic_compiler_longrun import run_compiler_longrun


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _split_ints(value: str | None) -> list[int]:
    if not value:
        return []
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0.9.5 compiler-backed arithmetic longrun.")
    parser.add_argument("--records-dir", required=True)
    parser.add_argument("--fresh-records", required=True)
    parser.add_argument("--dataset-dir", required=True)
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--modes", default="quick")
    parser.add_argument("--supported-samples", type=int, default=50000)
    parser.add_argument("--boundary-samples", type=int, default=50000)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--seeds", default=None)
    parser.add_argument("--timeout-seconds", type=int, default=5)
    parser.add_argument("--worker-count", type=int, default=8)
    parser.add_argument("--compile-worker-count", type=int, default=4)
    parser.add_argument("--max-runtime-hours", type=float, default=None)
    parser.add_argument("--checkpoint-interval-minutes", type=int, default=15)
    args = parser.parse_args()

    seeds = _split_ints(args.seeds)
    if args.seed is not None:
        seeds = [args.seed]
    if not seeds:
        seeds = [48]

    metrics = run_compiler_longrun(
        records_dir=args.records_dir,
        fresh_records=args.fresh_records,
        dataset_dir=args.dataset_dir,
        output_records=args.output_records,
        modes=_split_csv(args.modes),
        supported_samples=args.supported_samples,
        boundary_samples=args.boundary_samples,
        seeds=seeds,
        timeout_seconds=args.timeout_seconds,
        worker_count=args.worker_count,
        compile_worker_count=args.compile_worker_count,
        max_runtime_hours=args.max_runtime_hours,
        checkpoint_interval_minutes=args.checkpoint_interval_minutes,
    )
    print(json.dumps({
        "backend_type": metrics.get("backend_type"),
        "modes_completed": metrics.get("modes_completed"),
        "modes_partial_skipped": metrics.get("modes_partial_skipped"),
        "real_compiler_invocation_count": metrics.get("real_compiler_invocation_count"),
        "compiler_verified_correct_rate": metrics.get("compiler_verified_correct_rate"),
        "recommended_claim_level": metrics.get("recommended_claim_level"),
        "blocking_issues": metrics.get("blocking_issues"),
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
