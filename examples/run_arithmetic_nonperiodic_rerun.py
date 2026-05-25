from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.arithmetic_nonperiodic_rerun import run_nonperiodic_arithmetic_rerun


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _split_int_csv(value: str | None) -> list[int]:
    if not value:
        return []
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the v0.9.3.2 non-periodic arithmetic rerun.")
    parser.add_argument("--dataset-dir", required=True)
    parser.add_argument("--records-dir", required=True)
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--modes", default="quick")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--seeds", default=None)
    parser.add_argument("--heldout-samples", type=int, default=8000)
    parser.add_argument("--boundary-samples", type=int, default=8000)
    parser.add_argument("--beam-size", type=int, default=8)
    args = parser.parse_args()

    seeds = _split_int_csv(args.seeds)
    if args.seed is not None:
        seeds = [args.seed]
    if not seeds:
        seeds = [42]

    metrics = run_nonperiodic_arithmetic_rerun(
        dataset_dir=args.dataset_dir,
        records_dir=args.records_dir,
        output_records=args.output_records,
        modes=_split_csv(args.modes),
        seeds=seeds,
        heldout_samples=args.heldout_samples,
        boundary_samples=args.boundary_samples,
        beam_size=args.beam_size,
    )
    print(json.dumps({
        "modes_completed": metrics.get("modes_completed"),
        "recommended_claim_level": metrics.get("recommended_claim_level"),
        "candidate_trace_path": metrics.get("candidate_trace_path"),
        "periodic_rule_detected": metrics.get("periodic_rule_detected"),
        "fixed_value_detected": metrics.get("fixed_value_detected"),
        "summary_only_detected": metrics.get("summary_only_detected"),
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
