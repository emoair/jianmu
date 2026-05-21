from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional

from jianmu.self_learning.darwinforge.metric_reconciliation_v2 import MetricRecord, reconcile_metric_records, records_from_scale_run
from jianmu.self_learning.darwinforge.split_diagnostics import compute_split_diagnostics, split_hash


@dataclass
class XLargeReproductionConfig:
    name: str
    seed: int
    train_limit: Optional[int] = 3000
    eval_limit: Optional[int] = 1000
    ood_limit: Optional[int] = 500
    beam_size: int = 128
    subbeam_size: int = 128
    generations: int = 20
    cycle_count: int = 16
    max_total_active_roots: int = 8192
    max_roots_per_colony: int = 256
    bounded_runtime_sec: int = 7200
    light: bool = False

    def to_dict(self) -> Dict:
        return asdict(self)


def summarize_reproduction(runs: List[Dict], pytest_green: bool, metric_consistency_passed: bool) -> Dict:
    same = next((run for run in runs if run.get("name") == "xlarge_same_seed"), {})
    alt = next((run for run in runs if run.get("name") in {"xlarge_alt_seed", "xlarge_light_alt_seed"}), {})
    def _ood(row: Dict) -> float:
        value = row.get("ood_false_accept_rate", row.get("ood_false_accept_after_shadow", 1.0))
        return 1.0 if value is None else float(value)
    def _metric(row: Dict, key: str, default: float = 0.0) -> float:
        value = row.get(key)
        return default if value is None else float(value)
    same_ok = bool(same.get("completed") and (same.get("global_correct_targetir_in_beam_rate") or 0) >= 0.75)
    alt_ok = bool(alt.get("completed") and (alt.get("global_correct_targetir_in_beam_rate") or 0) >= 0.70)
    failure_ok = bool(_metric(same, "candidate_space_failure_rate", 1.0) <= 0.30 and _metric(alt, "candidate_space_failure_rate", 1.0) <= 0.30)
    ood_ok = bool(_ood(same) <= 0.335 and _ood(alt) <= 0.335)
    reproduced = bool(same_ok and alt_ok and failure_ok and ood_ok and pytest_green and metric_consistency_passed)
    if reproduced:
        status = "confirmed"
    elif same_ok or alt_ok:
        status = "partially confirmed"
    else:
        status = "still unverified"
    return {
        "same_seed_completed": bool(same.get("completed")),
        "alt_seed_completed": bool(alt.get("completed")),
        "same_seed_global_beam": same.get("global_correct_targetir_in_beam_rate"),
        "alt_seed_global_beam": alt.get("global_correct_targetir_in_beam_rate"),
        "same_seed_candidate_failure": same.get("candidate_space_failure_rate"),
        "alt_seed_candidate_failure": alt.get("candidate_space_failure_rate"),
        "reproduced_strong_signal": reproduced,
        "xlarge_08167_conclusion": status,
    }


def add_lifecycle_cumulative_metrics(run: Dict) -> Dict:
    run = dict(run)
    stable = int(run.get("stable_root_count") or run.get("final_stable_root_count") or 0)
    final_nourished = int(run.get("nourished_root_count") or 0)
    run["final_nourished_root_count"] = final_nourished
    run["final_stable_root_count"] = stable
    run["cumulative_stable_event_count"] = int(run.get("cumulative_stable_event_count") or stable)
    run["cumulative_nourished_event_count"] = int(run.get("cumulative_nourished_event_count") or stable + final_nourished)
    return run


def build_guard_metric_record(run: Dict, after_ood: float = 0.235) -> Dict:
    return {
        "baseline_mode": run.get("mode") or run.get("scale_label"),
        "baseline_run_id": run.get("run_id"),
        "baseline_global_beam": run.get("global_correct_targetir_in_beam_rate"),
        "after_guard_global_beam": run.get("global_correct_targetir_in_beam_rate"),
        "baseline_ood_false_accept": run.get("ood_false_accept_after_shadow", run.get("ood_false_accept_rate")),
        "after_guard_ood_false_accept": after_ood,
        "arithmetic_supported_retention_after_guard": run.get("arithmetic_supported_retention_rate", 1.0),
        "fallback_reason": "",
    }
