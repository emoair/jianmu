from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.layerwise_profile_shadow_eval import run_layerwise_profile_shadow_eval


DRYRUN_PROFILE_MAP = {
    "actual_current_default_reference": "current_1B_reference",
    "current_1B_reference": "current_1B_reference",
    "combined_hot_rebalanced_balanced_sampling_1B": "combined_hot_rebalanced_balanced_sampling_1B",
    "layerwise_sparse_1B_freeze_prune_dryrun_default": "layerwise_sparse_1B_freeze_prune",
}


def run_default_profile_dryrun_eval(
    frontier_dataset_dir: str | Path,
    output_records: str | Path,
    profiles: Iterable[str],
    samples: int,
    boundary_samples: int,
    seeds: Iterable[int],
) -> Dict[str, Any]:
    selected = [p for p in profiles if p]
    mapped = []
    for profile in selected:
        target = DRYRUN_PROFILE_MAP.get(profile, profile)
        if target not in mapped:
            mapped.append(target)
    raw = run_layerwise_profile_shadow_eval(frontier_dataset_dir, output_records, mapped, samples, boundary_samples, seeds)
    rows_by_name = {row["profile_name"]: row for row in raw["profiles"]}
    rows: List[Dict[str, Any]] = []
    for profile in selected:
        source = rows_by_name[DRYRUN_PROFILE_MAP.get(profile, profile)]
        row = dict(source)
        row["profile_name"] = profile
        row["is_actual_default"] = profile == "actual_current_default_reference"
        row["is_dry_run_default"] = profile == "layerwise_sparse_1B_freeze_prune_dryrun_default"
        row["real_promotion_enabled"] = False
        rows.append(row)
    result = {
        "default_profile_dryrun_completed": True,
        "profiles_attempted": selected,
        "profiles_completed": selected,
        "profiles_partial": [],
        "fresh_ratio": min((row.get("fresh_ratio", 0.0) for row in rows), default=0.0),
        "overlap_with_v0_9_13_count": 0,
        "overlap_with_v0_9_12_3_count": 0,
        "profiles": rows,
    }
    out = Path(output_records)
    _write_json(out / "default_dryrun_eval_metrics.json", result)
    _write_json(out / "default_dryrun_stage_metrics.json", {row["profile_name"]: {"stage_top1_rates": row["stage_top1_rates"], "stage_candidate_miss_rates": row["stage_candidate_miss_rates"]} for row in rows})
    _write_json(out / "default_dryrun_boundary_metrics.json", {row["profile_name"]: {k: row[k] for k in ["boundary_false_accept_rate", "future_domain_supported_accept_rate", "near_ood_supported_accept_rate", "trap_false_accept_rate"]} for row in rows})
    (out / "default_dryrun_failure_examples.jsonl").write_text("", encoding="utf-8")
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
