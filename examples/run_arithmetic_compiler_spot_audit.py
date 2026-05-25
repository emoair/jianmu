from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.arithmetic_compiler_spot_audit import run_real_compiler_arithmetic_spot_audit


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _split_int_csv(value: str | None) -> list[int]:
    if not value:
        return []
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0.9.4 real compiler arithmetic spot audit.")
    parser.add_argument("--records-dir", required=True)
    parser.add_argument("--dataset-dir", required=True)
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--modes", default="quick")
    parser.add_argument("--supported-samples", type=int, default=2000)
    parser.add_argument("--boundary-samples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--seeds", default=None)
    parser.add_argument("--timeout-seconds", type=int, default=5)
    args = parser.parse_args()

    seeds = _split_int_csv(args.seeds)
    if args.seed is not None:
        seeds = [args.seed]
    if not seeds:
        seeds = [42]

    metrics = run_real_compiler_arithmetic_spot_audit(
        records_dir=args.records_dir,
        dataset_dir=args.dataset_dir,
        output_records=args.output_records,
        modes=_split_csv(args.modes),
        supported_samples=args.supported_samples,
        boundary_samples=args.boundary_samples,
        seeds=seeds,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps({
        "backend_type": metrics.get("backend_type"),
        "compiler_name": metrics.get("compiler_name"),
        "real_compiler_invocation_count": metrics.get("real_compiler_invocation_count"),
        "compiler_verified_correct_rate": metrics.get("compiler_verified_correct_rate"),
        "recommended_claim_level": metrics.get("recommended_claim_level"),
        "blocking_issues": metrics.get("blocking_issues"),
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
