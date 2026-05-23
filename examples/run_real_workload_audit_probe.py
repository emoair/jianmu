from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.real_workload_audit import audit_v0_9_1_records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-records", default="records/v0_9_1")
    parser.add_argument("--output-records", default="records/v0_9_1_1")
    parser.add_argument("--dataset-dir", default="datasets/v0_8_5_boundary_aware")
    parser.add_argument("--audit-existing", default="true")
    parser.add_argument("--run-real-mini", default="true")
    parser.add_argument("--real-mini-train", type=int, default=500)
    parser.add_argument("--real-mini-eval", type=int, default=200)
    parser.add_argument("--real-mini-external-ood", type=int, default=200)
    parser.add_argument("--seeds", default="42")
    parser.add_argument("--worker-count", type=int, default=4)
    parser.add_argument("--compile-worker-count", type=int, default=2)
    args = parser.parse_args()

    result = audit_v0_9_1_records(
        source_records=args.source_records,
        output_records=args.output_records,
        dataset_dir=args.dataset_dir,
        run_real_mini=_flag(args.run_real_mini),
        real_mini_train=args.real_mini_train,
        real_mini_eval=args.real_mini_eval,
        real_mini_external_ood=args.real_mini_external_ood,
        seeds=[int(part.strip()) for part in args.seeds.split(",") if part.strip()],
        worker_count=args.worker_count,
        compile_worker_count=args.compile_worker_count,
    )
    print(json.dumps(result["readiness"], ensure_ascii=False, indent=2, sort_keys=True))


def _flag(value: str) -> bool:
    return str(value).lower() in {"1", "true", "yes", "y"}


if __name__ == "__main__":
    main()
