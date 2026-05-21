from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List

from jianmu.self_learning.datasets.sharded_dataset_loader import load_dataset_split


SLICE_LABELS = {
    "heldout_current_supported": {"current_supported"},
    "heldout_hard_ood": {"hard_ood"},
    "heldout_true_false_accept_trap": {"true_false_accept_trap"},
    "heldout_future_domain_candidate": {"future_domain_candidate"},
    "heldout_near_ood_generalization_candidate": {"near_ood_generalization_candidate"},
}


def build_heldout_boundary_slices(dataset_scale_dir: str | Path, eval_limit: int = 1000, seed: int = 42) -> Dict:
    dataset_scale_dir = Path(dataset_scale_dir)
    train_path = dataset_scale_dir / "train.jsonl"
    eval_paths = [
        dataset_scale_dir / "eval_seen_target_unseen_paraphrase.jsonl",
        dataset_scale_dir / "eval_unseen_target.jsonl",
        dataset_scale_dir / "eval_ood_boundary.jsonl",
        dataset_scale_dir / "eval_future_domain.jsonl",
        dataset_scale_dir / "eval_near_ood.jsonl",
    ]
    train = load_dataset_split(train_path, seed=seed) if train_path.exists() else []
    eval_rows: List[Dict] = []
    for path in eval_paths:
        if path.exists():
            eval_rows.extend(load_dataset_split(path, seed=seed))
    train_inputs = {row.get("raw_text") for row in train}
    train_paraphrases = {row.get("paraphrase_group_id") for row in train if row.get("paraphrase_group_id")}
    train_targets = {row.get("target_group_id") for row in train if row.get("target_group_id")}
    leakage_issues = []
    for row in eval_rows:
        if row.get("raw_text") in train_inputs:
            leakage_issues.append({"sample_id": row.get("sample_id"), "issue": "input_leakage"})
        if row.get("paraphrase_group_id") and row.get("paraphrase_group_id") in train_paraphrases:
            leakage_issues.append({"sample_id": row.get("sample_id"), "issue": "paraphrase_group_leakage"})
        if row.get("boundary_label") == "current_supported" and row.get("target_group_id") and row.get("target_group_id") in train_targets:
            leakage_issues.append({"sample_id": row.get("sample_id"), "issue": "target_group_leakage"})
    slices = {}
    per_label_limit = max(1, eval_limit // 5)
    for name, labels in SLICE_LABELS.items():
        slices[name] = [row for row in eval_rows if row.get("boundary_label") in labels][:per_label_limit]
    mixed = _round_robin(list(slices.values()), eval_limit)
    slices["heldout_mixed_boundary"] = mixed
    counts = {name: len(rows) for name, rows in slices.items()}
    return {
        "slices": slices,
        "heldout_slice_counts": counts,
        "boundary_label_distribution": dict(Counter(row.get("boundary_label") for row in mixed)),
        "leakage_check_passed": not leakage_issues,
        "leakage_issues": leakage_issues[:50],
        "actual_count_reason": {name: "available" if count else "empty_slice" for name, count in counts.items()},
    }


def manifest_without_samples(slice_result: Dict) -> Dict:
    return {
        "heldout_slice_counts": slice_result.get("heldout_slice_counts", {}),
        "boundary_label_distribution": slice_result.get("boundary_label_distribution", {}),
        "leakage_check_passed": slice_result.get("leakage_check_passed", False),
        "leakage_issues": slice_result.get("leakage_issues", []),
    }


def _round_robin(groups: Iterable[List[Dict]], limit: int) -> List[Dict]:
    groups = [list(group) for group in groups]
    selected = []
    idx = 0
    while len(selected) < limit and any(idx < len(group) for group in groups):
        for group in groups:
            if idx < len(group) and len(selected) < limit:
                selected.append(group[idx])
        idx += 1
    return selected
