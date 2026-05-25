from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.arithmetic_signal_audit import run_arithmetic_signal_audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-dir", default="records/v0_9_3")
    parser.add_argument("--dataset-dir", default="datasets/v0_9_2_arithmetic_curriculum")
    parser.add_argument("--output-records", default="records/v0_9_3_1")
    parser.add_argument("--run-targeted-rerun", default="true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--heldout-samples", type=int, default=1000)
    parser.add_argument("--boundary-samples", type=int, default=1000)
    args = parser.parse_args()
    result = run_arithmetic_signal_audit(
        args.records_dir,
        args.dataset_dir,
        args.output_records,
        _flag(args.run_targeted_rerun),
        args.seed,
        args.heldout_samples,
        args.boundary_samples,
    )
    print(json.dumps(result["readiness"], ensure_ascii=False, indent=2, sort_keys=True))


def _flag(value: str) -> bool:
    return str(value).lower() in {"1", "true", "yes", "y"}


if __name__ == "__main__":
    main()
