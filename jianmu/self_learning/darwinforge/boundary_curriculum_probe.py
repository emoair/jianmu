from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from jianmu.self_learning.datasets.boundary_dataset_audit import audit_boundary_dataset
from jianmu.self_learning.datasets.boundary_labels import BoundaryLabel
from jianmu.self_learning.datasets.nutrient_policy_labels import boundary_reward_policy_valid


def run_boundary_curriculum_probe(dataset_dir: str | Path) -> Dict:
    dataset_dir = Path(dataset_dir)
    splits = {}
    for name in [
        "train",
        "eval_seen_target_unseen_paraphrase",
        "eval_unseen_target",
        "eval_ood_boundary",
        "eval_future_domain",
        "eval_near_ood",
    ]:
        path = dataset_dir / f"{name}.jsonl"
        splits[name] = _read_jsonl(path)
    audit = audit_boundary_dataset(splits)
    all_rows = [row for rows in splits.values() for row in rows]
    valid_policy = sum(1 for row in all_rows if boundary_reward_policy_valid(row))
    counts = {label.value: sum(1 for row in all_rows if row.get("boundary_label") == label.value) for label in BoundaryLabel}
    return {
        "dataset_load_success": bool(all_rows),
        "audit_passed": audit["audit_passed"],
        "curriculum_stage_count": 6,
        "current_supported_count": counts[BoundaryLabel.CURRENT_SUPPORTED.value],
        "hard_ood_count": counts[BoundaryLabel.HARD_OOD.value],
        "true_false_accept_trap_count": counts[BoundaryLabel.TRUE_FALSE_ACCEPT_TRAP.value],
        "future_domain_candidate_count": counts[BoundaryLabel.FUTURE_DOMAIN_CANDIDATE.value],
        "near_ood_candidate_count": counts[BoundaryLabel.NEAR_OOD_GENERALIZATION_CANDIDATE.value],
        "boundary_reward_policy_valid": valid_policy == len(all_rows),
        "non_supported_targetir_leak_count": audit["non_supported_has_targetir_count"],
        "future_domain_train_current_leak_count": audit["future_domain_in_train_current_count"],
        "near_ood_train_current_leak_count": audit["near_ood_in_train_current_count"],
        "sample_pipeline_success_rate": round(valid_policy / max(len(all_rows), 1), 6),
    }


def _read_jsonl(path: Path):
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows
