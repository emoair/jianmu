from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jianmu.self_learning.darwinforge.multiagent_raw_dataset_audit import run_multiagent_raw_dataset_audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--previous-records", default="records/v0_9_15")
    parser.add_argument("--output-records", default="records/v0_9_15_1")
    parser.add_argument("--output-dataset", default="datasets/v0_9_15_1_multiagent_active_generation_audit")
    parser.add_argument("--supported-spot", type=int, default=5000)
    parser.add_argument("--boundary-spot", type=int, default=5000)
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--run-compiler-audit", default="true")
    parser.add_argument("--progress", default="false")
    parser.add_argument("--seed", type=int, default=97)
    args = parser.parse_args()
    result = run_multiagent_raw_dataset_audit(
        raw_dir=args.raw_dir,
        previous_records=args.previous_records,
        output_records=args.output_records,
        output_dataset=args.output_dataset,
        supported_spot=args.supported_spot,
        boundary_spot=args.boundary_spot,
        compile_worker_count=args.compile_worker_count,
        run_compiler_audit_enabled=str(args.run_compiler_audit).lower() == "true",
        seed=args.seed,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
