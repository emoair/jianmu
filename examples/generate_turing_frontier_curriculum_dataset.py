from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.turing_frontier_dataset_audit import audit_turing_frontier_dataset
from jianmu.self_learning.darwinforge.turing_frontier_generator import generate_turing_frontier_dataset


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="datasets/v0_9_9_turing_frontier_curriculum")
    parser.add_argument("--records-dir", default="records/v0_9_9")
    parser.add_argument("--scales", default="small,medium,large")
    parser.add_argument("--seed", type=int, default=68)
    parser.add_argument("--shard-size", type=int, default=10000)
    args = parser.parse_args()
    scales = [part.strip() for part in args.scales.split(",") if part.strip()]
    generation = generate_turing_frontier_dataset(args.output_dir, args.records_dir, scales, args.seed, args.shard_size)
    audit = audit_turing_frontier_dataset(args.output_dir, args.records_dir, scales)
    print(json.dumps({"scales_completed": generation["scales_completed"], "audit_passed_by_scale": audit["audit_passed_by_scale"]}, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

