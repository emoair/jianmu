from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable

from jianmu.self_learning.darwinforge.turing_substrate_boundary_labels import SUPPORTED


def audit_turing_substrate_dataset(scale_dir: str | Path) -> Dict[str, Any]:
    rows = list(_iter_rows(Path(scale_dir)))
    split_count = Counter(row["split"] for row in rows)
    category_count = Counter(row["category"] for row in rows)
    stage_count = Counter(row["stage"] for row in rows)
    seen_inputs: set[str] = set()
    seen_canonical: set[str] = set()
    split_inputs = defaultdict(set)
    group_splits = {
        "program_group_id": defaultdict(set),
        "control_flow_group_id": defaultdict(set),
        "target_group_id": defaultdict(set),
    }
    counters = Counter()
    for row in rows:
        inp = row.get("input", "")
        if inp in seen_inputs:
            counters["duplicate_input_count"] += 1
        seen_inputs.add(inp)
        split_inputs[row["split"]].add(inp)
        canonical = row.get("canonical_program")
        if canonical:
            if canonical in seen_canonical:
                counters["duplicate_canonical_program_count"] += 1
            seen_canonical.add(canonical)
        for key, bucket in group_splits.items():
            value = row.get(key)
            if value:
                bucket[value].add(row["split"])
        supported = row["category"] == SUPPORTED
        features = row.get("language_features", {})
        compiler = row.get("compiler_expectation", {})
        if not supported and row.get("target_ir") is not None:
            counters["non_supported_has_targetir_count"] += 1
        if not supported and row.get("expected_output") is not None:
            counters["non_supported_has_expected_output_count"] += 1
        if supported and row.get("target_ir") is None:
            counters["supported_missing_targetir_count"] += 1
        if supported and row.get("expected_output") is None:
            counters["supported_missing_expected_output_count"] += 1
        if not supported and (compiler.get("should_compile") or compiler.get("should_run") or compiler.get("expected_stdout") is not None):
            counters["unsupported_has_compiler_expectation_count"] += 1
        lower = inp.lower()
        if supported and ("while(true)" in lower or "while (true)" in lower or "while (" in lower and "fuel" not in lower and "whileboundedfuel" not in json.dumps(row.get("target_ir", {})).lower()):
            counters["unbounded_loop_supported_count"] += 1
        if supported and features.get("has_recursion"):
            counters["recursion_supported_count"] += 1
        if supported and features.get("has_pointer"):
            counters["pointer_supported_count"] += 1
        if supported and features.get("has_array"):
            counters["array_supported_count"] += 1
        if supported and features.get("has_function"):
            counters["function_supported_count"] += 1
        if supported and " / 0" in (canonical or ""):
            counters["division_by_zero_supported_count"] += 1
        if supported and "7 / 2" in (canonical or ""):
            counters["non_integer_division_supported_count"] += 1
        if supported and row.get("complexity", {}).get("overflow_risk"):
            counters["overflow_risk_supported_count"] += 1
        expected_text = str(row.get("expected_output") or "").strip()
        if expected_text and (f"answer is {expected_text}" in lower or f"output {expected_text}" in lower):
            counters["input_contains_expected_output_count"] += 1
        if _ir_has_c_source(row.get("target_ir")):
            counters["target_ir_contains_c_source_count"] += 1
        if row["category"] == "label_review_candidate" and row["split"] == "train":
            counters["label_review_in_train_count"] += 1
        if row["category"] == "future_domain_candidate" and row.get("training_usage") == "train_current":
            counters["future_domain_in_train_current_count"] += 1
        if row["category"] == "near_ood_program" and row.get("training_usage") == "train_current":
            counters["near_ood_in_train_current_count"] += 1
    train_eval = len(split_inputs["train"] & split_inputs["eval"])
    train_test = len(split_inputs["train"] & split_inputs["test"])
    counters["train_eval_input_leakage_count"] = train_eval
    counters["train_test_input_leakage_count"] = train_test
    counters["program_group_leakage_count"] = _group_leakage_count(group_splits["program_group_id"])
    counters["control_flow_group_leakage_count"] = _group_leakage_count(group_splits["control_flow_group_id"])
    counters["target_group_leakage_count"] = _group_leakage_count(group_splits["target_group_id"])
    blocking_keys = [
        "duplicate_input_count",
        "train_eval_input_leakage_count",
        "train_test_input_leakage_count",
        "program_group_leakage_count",
        "control_flow_group_leakage_count",
        "target_group_leakage_count",
        "non_supported_has_targetir_count",
        "non_supported_has_expected_output_count",
        "supported_missing_targetir_count",
        "supported_missing_expected_output_count",
        "unbounded_loop_supported_count",
        "recursion_supported_count",
        "pointer_supported_count",
        "array_supported_count",
        "function_supported_count",
        "division_by_zero_supported_count",
        "non_integer_division_supported_count",
        "overflow_risk_supported_count",
        "input_contains_expected_output_count",
        "label_review_in_train_count",
    ]
    blocking_issue_count = sum(1 for key in blocking_keys if counters[key])
    audit = {
        "total_count": len(rows),
        "split_count": dict(split_count),
        "category_count": dict(category_count),
        "stage_count": dict(stage_count),
        "warning_count": counters["duplicate_canonical_program_count"],
        "blocking_issue_count": blocking_issue_count,
        "audit_passed": blocking_issue_count == 0,
    }
    for key in [
        "duplicate_input_count",
        "duplicate_canonical_program_count",
        "train_eval_input_leakage_count",
        "train_test_input_leakage_count",
        "program_group_leakage_count",
        "control_flow_group_leakage_count",
        "target_group_leakage_count",
        "non_supported_has_targetir_count",
        "non_supported_has_expected_output_count",
        "supported_missing_targetir_count",
        "supported_missing_expected_output_count",
        "unsupported_has_compiler_expectation_count",
        "unbounded_loop_supported_count",
        "recursion_supported_count",
        "pointer_supported_count",
        "array_supported_count",
        "function_supported_count",
        "division_by_zero_supported_count",
        "non_integer_division_supported_count",
        "overflow_risk_supported_count",
        "input_contains_expected_output_count",
        "target_ir_contains_c_source_count",
        "label_review_in_train_count",
        "future_domain_in_train_current_count",
        "near_ood_in_train_current_count",
    ]:
        audit[key] = counters[key]
    return audit


def write_audit_report(scale_dir: str | Path, audit: Dict[str, Any]) -> None:
    Path(scale_dir, "report.md").write_text("\n".join([
        "# v0.9.6 Turing Substrate Curriculum Dataset Report",
        "",
        f"- total_count: {audit['total_count']}",
        f"- audit_passed: {audit['audit_passed']}",
        f"- blocking_issue_count: {audit['blocking_issue_count']}",
        f"- category_count: {audit['category_count']}",
        f"- split_count: {audit['split_count']}",
        "",
        "## Non-Claims",
        "- This dataset does not prove Turing completeness, solved program synthesis, or production readiness.",
    ]) + "\n", encoding="utf-8")


def _iter_rows(scale_dir: Path) -> Iterable[Dict[str, Any]]:
    for split in ["train", "eval", "test", "heldout"]:
        for path in sorted((scale_dir / split).glob("*.jsonl")):
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
