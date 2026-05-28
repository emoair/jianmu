from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jianmu.self_learning.darwinforge.chinese_dataset_factory import generate_codex_grammar_chinese_dataset


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", required=True)
    p.add_argument("--records-dir", required=True)
    p.add_argument("--scales", default="pilot,medium,large")
    p.add_argument("--seed", type=int, default=98)
    p.add_argument("--shard-size", type=int, default=10000)
    args = p.parse_args()
    result = generate_codex_grammar_chinese_dataset(args.output_dir, args.records_dir, args.scales.split(","), args.seed, args.shard_size)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
