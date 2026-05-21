from __future__ import annotations

from collections import Counter
from typing import Dict, List

from jianmu.self_learning.datasets.boundary_labels import BoundaryLabel, validate_boundary_sample


def audit_boundary_dataset(splits: Dict[str, List[Dict]]) -> Dict:
    all_rows = [row for rows in splits.values() for row in rows]
    inputs = [row.get("raw_text") for row in all_rows]
    ids = [row.get("sample_id") for row in all_rows]
    issues = []
    duplicate_input_count = len(inputs) - len(set(inputs))
    duplicate_sample_id_count = len(ids) - len(set(ids))
    if duplicate_input_count:
        issues.append({"severity": "blocking", "issue": "duplicate_input", "count": duplicate_input_count})
    if duplicate_sample_id_count:
        issues.append({"severity": "blocking", "issue": "duplicate_sample_id", "count": duplicate_sample_id_count})
    train_inputs = {row.get("raw_text") for row in splits.get("train", [])}
    eval_inputs = {row.get("raw_text") for name, rows in splits.items() if name != "train" for row in rows}
    train_eval_input_leakage_count = len(train_inputs & eval_inputs)
    if train_eval_input_leakage_count:
        issues.append({"severity": "blocking", "issue": "train_eval_input_leakage", "count": train_eval_input_leakage_count})
    missing_required = 0
    malformed = 0
    label_conflict = 0
    for row in all_rows:
        row_issues = validate_boundary_sample(row)
        missing_required += sum(1 for issue in row_issues if issue.startswith("missing_required_field"))
        malformed += bool(row_issues)
        label_conflict += sum(1 for issue in row_issues if issue in {"future_domain_in_train_current", "near_ood_in_train_current", "non_supported_has_targetir"})
    non_supported_has_targetir_count = sum(1 for row in all_rows if row.get("boundary_label") != BoundaryLabel.CURRENT_SUPPORTED.value and (row.get("target_ir") or row.get("expected_output")))
    future_domain_in_train_current_count = sum(1 for row in all_rows if row.get("boundary_label") == BoundaryLabel.FUTURE_DOMAIN_CANDIDATE.value and row.get("training_usage") == "train_current")
    near_ood_in_train_current_count = sum(1 for row in all_rows if row.get("boundary_label") == BoundaryLabel.NEAR_OOD_GENERALIZATION_CANDIDATE.value and row.get("training_usage") == "train_current")
    true_false_accept_has_positive_accept_reward_count = sum(1 for row in all_rows if row.get("boundary_label") == BoundaryLabel.TRUE_FALSE_ACCEPT_TRAP.value and row.get("accept_reward", 0) > 0)
    hard_ood_has_positive_accept_reward_count = sum(1 for row in all_rows if row.get("boundary_label") == BoundaryLabel.HARD_OOD.value and row.get("accept_reward", 0) > 0)
    current_supported = [row for row in all_rows if row.get("boundary_label") == BoundaryLabel.CURRENT_SUPPORTED.value]
    current_supported_has_targetir_rate = round(sum(1 for row in current_supported if row.get("target_ir") and row.get("expected_output")) / max(len(current_supported), 1), 6)
    paraphrase_group_leakage_count = _group_leakage(splits, "paraphrase_group_id")
    target_group_leakage_count = _group_leakage(splits, "target_group_id", only_current=True)
    if paraphrase_group_leakage_count:
        issues.append({"severity": "blocking", "issue": "paraphrase_group_leakage", "count": paraphrase_group_leakage_count})
    if target_group_leakage_count:
        issues.append({"severity": "blocking", "issue": "target_group_leakage", "count": target_group_leakage_count})
    blocking_values = [
        non_supported_has_targetir_count,
        future_domain_in_train_current_count,
        near_ood_in_train_current_count,
        true_false_accept_has_positive_accept_reward_count,
        hard_ood_has_positive_accept_reward_count,
        train_eval_input_leakage_count,
        paraphrase_group_leakage_count,
        target_group_leakage_count,
        duplicate_input_count,
        duplicate_sample_id_count,
        label_conflict,
        missing_required,
    ]
    blocking_issue_count = sum(1 for value in blocking_values if value)
    warning_count = 0
    return {
        "audit_passed": blocking_issue_count == 0,
        "blocking_issue_count": blocking_issue_count,
        "warning_count": warning_count,
        "issues": issues,
        "recommendations": [] if blocking_issue_count == 0 else ["fix blocking dataset issues before probe"],
        "duplicate_input_count": duplicate_input_count,
        "duplicate_sample_id_count": duplicate_sample_id_count,
        "train_eval_input_leakage_count": train_eval_input_leakage_count,
        "paraphrase_group_leakage_count": paraphrase_group_leakage_count,
        "target_group_leakage_count": target_group_leakage_count,
        "boundary_label_distribution": dict(Counter(row.get("boundary_label") for row in all_rows)),
        "expected_action_distribution": dict(Counter(row.get("expected_action") for row in all_rows)),
        "nutrient_policy_distribution": dict(Counter(policy for row in all_rows for policy in row.get("nutrient_policy", []))),
        "current_supported_has_targetir_rate": current_supported_has_targetir_rate,
        "non_supported_has_targetir_count": non_supported_has_targetir_count,
        "future_domain_in_train_current_count": future_domain_in_train_current_count,
        "near_ood_in_train_current_count": near_ood_in_train_current_count,
        "true_false_accept_has_positive_accept_reward_count": true_false_accept_has_positive_accept_reward_count,
        "hard_ood_has_positive_accept_reward_count": hard_ood_has_positive_accept_reward_count,
        "label_conflict_count": label_conflict,
        "missing_required_field_count": missing_required,
        "malformed_sample_count": malformed,
    }


def _group_leakage(splits: Dict[str, List[Dict]], field: str, only_current: bool = False) -> int:
    train = {
        row.get(field)
        for row in splits.get("train", [])
        if row.get(field) and (not only_current or row.get("boundary_label") == BoundaryLabel.CURRENT_SUPPORTED.value)
    }
    eval_groups = {
        row.get(field)
        for name, rows in splits.items()
        if name != "train"
        for row in rows
        if row.get(field) and (not only_current or row.get("boundary_label") == BoundaryLabel.CURRENT_SUPPORTED.value)
    }
    return len(train & eval_groups)
