from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.ironjudge_accounting_reconciliation import build_accounting_reconciliation
from jianmu.self_learning.darwinforge.ironjudge_main20k_completion import write_main20k_completion_not_needed
from jianmu.self_learning.darwinforge.ironjudge_reconciliation_readiness import write_clean_criteria, write_integrity, write_mainline, write_readiness


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-records-v18", required=True)
    parser.add_argument("--source-records-v18-1", required=True)
    parser.add_argument("--forgefrontier-dataset-dir", required=True)
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--accounting-mode", default="auto")
    parser.add_argument("--complete-main20k-if-needed", default="true")
    parser.add_argument("--target-main", type=int, default=20000)
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--fallback-worker-count", type=int, default=8)
    parser.add_argument("--timeout-seconds", type=int, default=5)
    parser.add_argument("--progress", default="false")
    parser.add_argument("--max-runtime-hours", type=float, default=8.0)
    parser.add_argument("--checkpoint-interval-minutes", type=int, default=10)
    parser.add_argument("--seed", type=int, default=113)
    args = parser.parse_args()
    del (
        args.forgefrontier_dataset_dir,
        args.complete_main20k_if_needed,
        args.target_main,
        args.compile_worker_count,
        args.fallback_worker_count,
        args.timeout_seconds,
        args.progress,
        args.max_runtime_hours,
        args.checkpoint_interval_minutes,
        args.seed,
    )
    reconciliation = build_accounting_reconciliation(args.source_records_v18, args.source_records_v18_1, args.output_records, args.accounting_mode)
    v181 = Path(args.source_records_v18_1)
    scaleup = json.loads((v181 / "ironjudge_resumable_scaleup.json").read_text(encoding="utf-8"))
    accounting = json.loads((v181 / "ironjudge_invocation_accounting.json").read_text(encoding="utf-8"))
    claim = json.loads((Path(args.output_records) / "ironjudge_claim_reconciliation.json").read_text(encoding="utf-8"))
    main20k = write_main20k_completion_not_needed(args.output_records, reconciliation)
    clean = write_clean_criteria(args.output_records, reconciliation, scaleup)
    integrity = write_integrity(args.output_records, accounting)
    readiness = write_readiness(args.output_records, reconciliation, claim, clean, integrity, main20k)
    mainline = write_mainline(args.output_records, reconciliation, readiness)
    print(json.dumps({"readiness": readiness, "mainline": mainline}, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
