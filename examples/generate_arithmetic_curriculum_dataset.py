from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.arithmetic_curriculum_generator import generate_arithmetic_curriculum_dataset


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="datasets/v0_9_2_arithmetic_curriculum")
    parser.add_argument("--records-dir", default="records/v0_9_2")
    parser.add_argument("--scales", default="small,medium")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--shard-size", type=int, default=10000)
    args = parser.parse_args()
    result = generate_arithmetic_curriculum_dataset(args.output_dir, args.records_dir, [part.strip() for part in args.scales.split(",") if part.strip()], args.seed, args.shard_size)
    print(json.dumps(result["scales"], ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
