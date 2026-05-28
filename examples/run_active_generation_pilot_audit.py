from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jianmu.self_learning.darwinforge.active_generation_pilot import run_active_generation_pilot


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dataset-dir", required=True)
    parser.add_argument("--output-dataset-dir", default="datasets/v0_9_15_active_generation_pilot")
    parser.add_argument("--records-dir", default="records/v0_9_15")
    parser.add_argument("--supported-spot", type=int, default=5000)
    parser.add_argument("--boundary-spot", type=int, default=5000)
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--seed", type=int, default=97)
    parser.add_argument("--timeout-seconds", type=int, default=5)
    args = parser.parse_args()
    result = run_active_generation_pilot(
        raw_dataset_dir=args.raw_dataset_dir,
        output_dataset_dir=args.output_dataset_dir,
        records_dir=args.records_dir,
        supported_spot=args.supported_spot,
        boundary_spot=args.boundary_spot,
        compile_worker_count=args.compile_worker_count,
        seed=args.seed,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
