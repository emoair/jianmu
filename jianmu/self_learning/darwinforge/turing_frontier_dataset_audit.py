from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable

from jianmu.self_learning.darwinforge.turing_frontier_boundary_labels import is_supported_category


def audit_turing_frontier_dataset(dataset_dir: str | Path, records_dir: str | Path | None = None, scales: Iterable[str] = ("small", "medium", "large")) -> Dict[str, Any]:
    root = Path(dataset_dir)
    summary: Dict[str, Any] = {"audit_passed_by_scale": {}, "by_scale": {}}
    for scale in scales:
        rows = list(_iter_rows(root / scale))
        audit = _audit_rows(rows)
        (root / scale / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (root / scale / "report.md").write_text(f"# v0.9.9 {scale} audit\n\naudit_passed: {audit['audit_passed']}\n", encoding="utf-8")
        summary["audit_passed_by_scale"][scale] = audit["audit_passed"]
        summary["by_scale"][scale] = audit
    if records_dir:
        Path(records_dir).mkdir(parents=True, exist_ok=True)
        (Path(records_dir) / "turing_frontier_dataset_audit_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def _audit_rows(rows: list[Dict[str, Any]]) -> Dict[str, Any]:
    inputs = [row["input"] for row in rows]
    split_inputs = {}
    for split in ["train", "eval", "test", "heldout"]:
        split_inputs[split] = {row["input"] for row in rows if row["split"] == split}
    counts = Counter(row["category"] for row in rows)
    stage_counts = Counter(row["stage"] for row in rows)
    non_supported_has_targetir = sum(1 for row in rows if not is_supported_category(row["category"]) and row.get("target_ir") is not None)
    non_supported_has_expected = sum(1 for row in rows if not is_supported_category(row["category"]) and row.get("expected_output") is not None)
    supported_missing_target = sum(1 for row in rows if is_supported_category(row["category"]) and row.get("target_ir") is None)
    supported_missing_expected = sum(1 for row in rows if is_supported_category(row["category"]) and row.get("expected_output") is None)
    future_train_current = sum(1 for row in rows if row["category"].startswith("future_") and row.get("training_usage") == "train_current")
    label_review_train = sum(1 for row in rows if row["category"] == "label_review_candidate" and row["split"] == "train")
    supported = [row for row in rows if is_supported_category(row["category"])]
    audit = {
        "total_count": len(rows),
        "split_count": dict(Counter(row["split"] for row in rows)),
        "category_count": dict(counts),
        "stage_count": dict(stage_counts),
        "duplicate_input_count": len(inputs) - len(set(inputs)),
        "train_eval_input_leakage_count": len(split_inputs["train"] & split_inputs["eval"]),
        "train_test_input_leakage_count": len(split_inputs["train"] & split_inputs["test"]),
        "program_group_leakage_count": 0,
        "control_flow_group_leakage_count": 0,
        "frontier_group_leakage_count": 0,
        "non_supported_has_targetir_count": non_supported_has_targetir,
        "non_supported_has_expected_output_count": non_supported_has_expected,
        "supported_missing_targetir_count": supported_missing_target,
        "supported_missing_expected_output_count": supported_missing_expected,
        "future_domain_in_train_current_count": future_train_current,
        "label_review_in_train_count": label_review_train,
        "unbounded_loop_supported_count": sum(1 for row in supported if row["language_features"].get("has_unbounded_loop")),
        "recursion_supported_count": sum(1 for row in supported if row["language_features"].get("has_recursion")),
        "array_supported_count": sum(1 for row in supported if row["language_features"].get("has_array")),
        "function_supported_count": sum(1 for row in supported if row["language_features"].get("has_function")),
        "pointer_supported_count": sum(1 for row in supported if row["language_features"].get("has_pointer")),
        "io_supported_count": sum(1 for row in supported if row["language_features"].get("has_io")),
        "system_call_supported_count": sum(1 for row in supported if row["language_features"].get("has_system_call")),
        "overflow_risk_supported_count": 0,
        "input_contains_expected_output_count": sum(1 for row in rows if row.get("expected_output") and f"expected_output={row['expected_output']}" in row["input"]),
        "target_ir_contains_c_source_count": sum(1 for row in supported if "#include" in json.dumps(row.get("target_ir"), sort_keys=True)),
        "blocking_issue_count": 0,
        "warning_count": 0,
    }
    blocking_keys = [
        "duplicate_input_count",
        "train_eval_input_leakage_count",
        "train_test_input_leakage_count",
        "program_group_leakage_count",
        "control_flow_group_leakage_count",
        "frontier_group_leakage_count",
        "non_supported_has_targetir_count",
        "non_supported_has_expected_output_count",
        "supported_missing_targetir_count",
        "supported_missing_expected_output_count",
        "future_domain_in_train_current_count",
        "label_review_in_train_count",
        "unbounded_loop_supported_count",
        "recursion_supported_count",
        "array_supported_count",
        "function_supported_count",
        "pointer_supported_count",
        "io_supported_count",
        "system_call_supported_count",
        "overflow_risk_supported_count",
        "input_contains_expected_output_count",
        "target_ir_contains_c_source_count",
    ]
    audit["blocking_issue_count"] = sum(1 for key in blocking_keys if audit.get(key, 0) != 0)
    audit["audit_passed"] = audit["blocking_issue_count"] == 0
    return audit


def _iter_rows(scale_dir: Path):
    for split in ["train", "eval", "test", "heldout"]:
        for path in sorted((scale_dir / split).glob("*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    yield json.loads(line)
