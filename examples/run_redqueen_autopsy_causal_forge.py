from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.redqueen_autopsy import run_redqueen_autopsy


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-records-v17", required=True)
    parser.add_argument("--source-records-v18", required=True)
    parser.add_argument("--source-records-v18-2", required=True)
    parser.add_argument("--redqueen-dataset-dir", required=True)
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--run-spec-attribution", default="true")
    parser.add_argument("--run-pattern-roi", default="true")
    parser.add_argument("--run-template-overfit-audit", default="true")
    parser.add_argument("--run-contrastive-pair-audit", default="true")
    parser.add_argument("--run-regression-sentinel", default="true")
    parser.add_argument("--run-causal-curriculum-plan", default="true")
    parser.add_argument("--run-bandit-design", default="true")
    parser.add_argument("--run-bandit-simulation", default="true")
    parser.add_argument("--progress", default="false")
    parser.add_argument("--seed", type=int, default=114)
    args = parser.parse_args()
    result = run_redqueen_autopsy(args.source_records_v17, args.source_records_v18, args.source_records_v18_2, args.redqueen_dataset_dir, args.output_records, args.seed)
    print(json.dumps(result["redqueen_autopsy_readiness"], ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
