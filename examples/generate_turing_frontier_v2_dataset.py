from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.turing_frontier_v2_audit import audit_turing_frontier_v2_dataset
from jianmu.self_learning.darwinforge.turing_frontier_v2_coverage import summarize_turing_frontier_v2_coverage
from jianmu.self_learning.darwinforge.turing_frontier_v2_generator import generate_turing_frontier_v2_dataset


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--records-dir", required=True)
    parser.add_argument("--scales", default="pilot,medium,large")
    parser.add_argument("--seed", type=int, default=96)
    parser.add_argument("--shard-size", type=int, default=10000)
    args = parser.parse_args()
    generation = generate_turing_frontier_v2_dataset(args.output_dir, args.records_dir, [s for s in args.scales.split(",") if s], args.seed, args.shard_size)
    audit = audit_turing_frontier_v2_dataset(args.output_dir, args.records_dir)
    coverage = summarize_turing_frontier_v2_coverage(args.output_dir, args.records_dir)
    print(json.dumps({"scales": list(generation["scales"].keys()), "audit_passed": all(row["audit_passed"] for row in audit["scales"].values()), "coverage_completed": coverage["dataset_v2_coverage_completed"]}, indent=2))


if __name__ == "__main__":
    main()
