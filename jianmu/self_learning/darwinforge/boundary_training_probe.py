from __future__ import annotations

from pathlib import Path
from typing import Dict

from jianmu.self_learning.darwinforge.boundary_curriculum_runner import run_boundary_curriculum_runner
from jianmu.self_learning.datasets.sharded_dataset_loader import load_dataset_split_with_report


def run_boundary_training_probe(dataset_scale_dir: str | Path, mode: str = "quick", worker_count: int = 4) -> Dict:
    dataset_scale_dir = Path(dataset_scale_dir)
    train_report = load_dataset_split_with_report(dataset_scale_dir / "train.jsonl")
    eval_rows = []
    eval_reports = []
    for split in ["eval_seen_target_unseen_paraphrase", "eval_unseen_target", "eval_ood_boundary", "eval_future_domain", "eval_near_ood"]:
        report = load_dataset_split_with_report(dataset_scale_dir / f"{split}.jsonl")
        eval_reports.append({k: v for k, v in report.items() if k != "records"})
        eval_rows.extend(report["records"])
    run = run_boundary_curriculum_runner(train_report["records"], eval_rows, mode=mode, worker_count=worker_count)
    return {
        **run,
        "dataset_load_success": bool(train_report["records"]) and bool(eval_rows),
        "train_loader_report": {k: v for k, v in train_report.items() if k != "records"},
        "eval_loader_reports": eval_reports,
    }
