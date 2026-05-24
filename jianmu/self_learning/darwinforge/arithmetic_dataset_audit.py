from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List


def audit_arithmetic_dataset(scale_dir: str | Path) -> Dict[str, Any]:
    rows = list(_iter_rows(Path(scale_dir)))
    split_count = Counter(row["split"] for row in rows)
    category_count = Counter(row["category"] for row in rows)
    stage_count = Counter(row["stage"] for row in rows)
    input_seen: Dict[str, str] = {}
    dup_input = 0
    canon_seen: set[str] = set()
    dup_canon = 0
    by_split_inputs = defaultdict(set)
    group_splits = {"expression_group_id": defaultdict(set), "paraphrase_group_id": defaultdict(set), "target_group_id": defaultdict(set)}
    counters = Counter()
    for row in rows:
        inp = row["input"]
        if inp in input_seen:
            dup_input += 1
        input_seen[inp] = row["id"]
        by_split_inputs[row["split"]].add(inp)
        canon = row.get("canonical_expression")
        if canon:
            if canon in canon_seen:
                dup_canon += 1
            canon_seen.add(canon)
        for key, buckets in group_splits.items():
            value = row.get(key)
            if value:
                buckets[value].add(row["split"])
        supported = row["category"] == "current_supported_arithmetic"
        if not supported and row.get("target_ir") is not None:
            counters["non_supported_has_targetir_count"] += 1
        if not supported and row.get("expected_output") is not None:
            counters["non_supported_has_expected_output_count"] += 1
        if supported and row.get("target_ir") is None:
            counters["supported_missing_targetir_count"] += 1
        if supported and row.get("expected_output") is None:
            counters["supported_missing_expected_output_count"] += 1
        if supported and row.get("division_kind") == "division_by_zero":
            counters["division_by_zero_supported_count"] += 1
        if supported and row.get("division_kind") == "non_integer":
            counters["non_integer_division_supported_count"] += 1
        if _ir_has_c_source(row.get("target_ir")):
            counters["target_ir_contains_c_source_count"] += 1
        expected = row.get("expected_output")
        expected_text = str(expected).strip() if expected is not None else ""
        lowered_input = row.get("input", "").lower()
        if expected_text and (f"answer is {expected_text}" in lowered_input or f"= {expected_text}" in lowered_input or f"output {expected_text}" in lowered_input):
            counters["input_contains_expected_output_count"] += 1
        if any(field in row.get("input", "") for field in ["target_ir", "expected_output", "boundary_label", "expected_action", "nutrient_policy", "toxicity_policy", "target_branch_path"]):
            counters["forbidden_field_in_input_count"] += 1
        if row["category"] == "label_review_candidate" and row["split"] == "train":
            counters["label_review_in_train_count"] += 1
        if row["category"] == "future_domain_candidate" and row.get("training_usage") == "train_current":
            counters["future_domain_in_train_current_count"] += 1
        if row["category"] == "near_ood_arithmetic" and row.get("training_usage") == "train_current":
            counters["near_ood_in_train_current_count"] += 1
        if not supported and row.get("boundary_label") == "current_supported":
            counters["unsupported_in_supported_count"] += 1
    train_eval = len(by_split_inputs["train"] & by_split_inputs["eval"])
    train_test = len(by_split_inputs["train"] & by_split_inputs["test"])
    expression_group_leakage = _group_leakage_count(group_splits["expression_group_id"])
    paraphrase_group_leakage = _group_leakage_count(group_splits["paraphrase_group_id"])
    target_group_leakage = _group_leakage_count(group_splits["target_group_id"])
    blocking = {
        "duplicate_input_count": dup_input,
        "train_eval_input_leakage_count": train_eval,
        "train_test_input_leakage_count": train_test,
        "expression_group_leakage_count": expression_group_leakage,
        "paraphrase_group_leakage_count": paraphrase_group_leakage,
        "target_group_leakage_count": target_group_leakage,
        **{key: counters[key] for key in [
            "non_supported_has_targetir_count",
            "non_supported_has_expected_output_count",
            "supported_missing_targetir_count",
            "supported_missing_expected_output_count",
            "division_by_zero_supported_count",
            "non_integer_division_supported_count",
            "input_contains_expected_output_count",
            "label_review_in_train_count",
        ]},
    }
    blocking_issue_count = sum(1 for value in blocking.values() if value)
    audit = {
        "total_count": len(rows),
        "split_count": dict(split_count),
        "category_count": dict(category_count),
        "stage_count": dict(stage_count),
        "duplicate_input_count": dup_input,
        "duplicate_canonical_expression_count": dup_canon,
        "train_eval_input_leakage_count": train_eval,
        "train_test_input_leakage_count": train_test,
        "expression_group_leakage_count": expression_group_leakage,
        "paraphrase_group_leakage_count": paraphrase_group_leakage,
        "target_group_leakage_count": target_group_leakage,
        "target_ir_contains_c_source_count": counters["target_ir_contains_c_source_count"],
        "forbidden_field_in_input_count": counters["forbidden_field_in_input_count"],
        "future_domain_in_train_current_count": counters["future_domain_in_train_current_count"],
        "near_ood_in_train_current_count": counters["near_ood_in_train_current_count"],
        "unsupported_in_supported_count": counters["unsupported_in_supported_count"],
        "blocking_issue_count": blocking_issue_count,
        "warning_count": dup_canon,
        "audit_passed": blocking_issue_count == 0,
        **{key: counters[key] for key in [
            "non_supported_has_targetir_count",
            "non_supported_has_expected_output_count",
            "supported_missing_targetir_count",
            "supported_missing_expected_output_count",
            "division_by_zero_supported_count",
            "non_integer_division_supported_count",
            "input_contains_expected_output_count",
            "label_review_in_train_count",
        ]},
    }
    return audit


def write_audit_report(scale_dir: str | Path, audit: Dict[str, Any]) -> None:
    path = Path(scale_dir) / "report.md"
    path.write_text("\n".join([
        "# v0.9.2 Arithmetic Curriculum Dataset Report",
        "",
        f"- total_count: {audit['total_count']}",
        f"- audit_passed: {audit['audit_passed']}",
        f"- blocking_issue_count: {audit['blocking_issue_count']}",
        f"- category_count: {audit['category_count']}",
        f"- split_count: {audit['split_count']}",
        "",
        "## Non-Claims",
        "- This dataset does not prove solved arithmetic, stable convergence, solved OOD, same-size LLM advantage, or safe real promotion.",
    ]) + "\n", encoding="utf-8")


def _iter_rows(scale_dir: Path) -> Iterable[Dict[str, Any]]:
    for split in ["train", "eval", "test", "heldout"]:
        split_dir = scale_dir / split
        for path in sorted(split_dir.glob("*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    yield json.loads(line)


def _group_leakage_count(groups: Dict[str, set[str]]) -> int:
    return sum(1 for splits in groups.values() if len(splits - {"heldout"}) > 1)


def _ir_has_c_source(node: Any) -> bool:
    if node is None:
        return False
    if isinstance(node, str):
        return "#include" in node or "printf" in node or "int main" in node
    if isinstance(node, dict):
        return any(_ir_has_c_source(value) for value in node.values())
    if isinstance(node, list):
        return any(_ir_has_c_source(value) for value in node)
    return False
