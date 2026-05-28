from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jianmu.self_learning.darwinforge.chinese_dataset_audit import audit_chinese_dataset
from jianmu.self_learning.darwinforge.chinese_dataset_compiler_audit import run_chinese_dataset_compiler_audit
from jianmu.self_learning.darwinforge.chinese_dataset_readiness import write_chinese_dataset_readiness


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dataset-dir", required=True)
    p.add_argument("--previous-raw-records")
    p.add_argument("--missing-multiagent-records")
    p.add_argument("--output-records", required=True)
    p.add_argument("--supported-spot", type=int, default=5000)
    p.add_argument("--boundary-spot", type=int, default=5000)
    p.add_argument("--compile-worker-count", type=int, default=16)
    p.add_argument("--run-compiler-audit", default="true")
    p.add_argument("--progress", default="false")
    p.add_argument("--seed", type=int, default=98)
    args = p.parse_args()
    audit = audit_chinese_dataset(args.dataset_dir, args.output_records)
    compiler = run_chinese_dataset_compiler_audit(args.dataset_dir, args.output_records, args.supported_spot, args.boundary_spot, args.compile_worker_count, args.seed) if str(args.run_compiler_audit).lower() == "true" else {"compiler_audit_completed": False, "compiler_verified_correct_rate": 0.0, "boundary_compiler_misroute_count": 0, "future_domain_compiled_count": 0, "english_compiled_count": 0, "mixed_language_compiled_count": 0}
    readiness = write_chinese_dataset_readiness(args.output_records, audit, compiler)
    print(json.dumps(readiness, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
