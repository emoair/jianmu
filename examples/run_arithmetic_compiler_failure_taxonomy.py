from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.arithmetic_compiler_failure_replay import (
    run_compiler_failure_taxonomy,
)


def _bool_arg(value: str) -> bool:
    return value.lower() in {"1", "true", "yes", "on"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0.9.4.2 compiler failure taxonomy.")
    parser.add_argument("--source-records", required=True)
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--dataset-dir", default="datasets/v0_9_2_arithmetic_curriculum")
    parser.add_argument("--rerun-failures", default="true")
    parser.add_argument("--allow-engineering-patch", default="true")
    parser.add_argument("--timeout-seconds", type=int, default=5)
    args = parser.parse_args()
    summary = run_compiler_failure_taxonomy(
        source_records=args.source_records,
        output_records=args.output_records,
        dataset_dir=args.dataset_dir,
        rerun_failures=_bool_arg(args.rerun_failures),
        allow_engineering_patch=_bool_arg(args.allow_engineering_patch),
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps({
        "original_failure_count": summary.get("original_failure_count"),
        "classified_failure_count": summary.get("classified_failure_count"),
        "dominant_failure_category": summary.get("dominant_failure_category"),
        "patched_compiler_verified_correct_rate": summary.get("patched_compiler_verified_correct_rate"),
        "recommended_claim_level": summary.get("recommended_claim_level"),
        "blocking_issues": summary.get("blocking_issues"),
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
