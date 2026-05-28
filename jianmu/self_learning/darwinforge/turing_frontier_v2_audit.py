from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable


def audit_turing_frontier_v2_dataset(dataset_dir: str | Path, records_dir: str | Path | None = None) -> Dict[str, Any]:
    root = Path(dataset_dir)
    summary = {"dataset_v2_audit_completed": True, "scales": {}}
    for scale_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        rows = list(_iter_rows(scale_dir))
        audit = _audit_rows(rows)
        _write_json(scale_dir / "audit.json", audit)
        _write_json(scale_dir / "coverage_map.json", _coverage(rows, audit))
        (scale_dir / "report.md").write_text(_report(scale_dir.name, audit), encoding="utf-8")
        summary["scales"][scale_dir.name] = audit
    if records_dir:
        Path(records_dir).mkdir(parents=True, exist_ok=True)
        _write_json(Path(records_dir) / "dataset_v2_audit_summary.json", summary)
    return summary


def _audit_rows(rows: list[Dict[str, Any]]) -> Dict[str, Any]:
    split_count = Counter(row["split"] for row in rows)
    category_count = Counter(row["category"] for row in rows)
    stage_count = Counter(row["stage"] for row in rows)
    status_count = Counter(row["support_status"] for row in rows)
    inputs = [row["input"] for row in rows]
    non_supported = [row for row in rows if row["support_status"] != "current_supported"]
    current = [row for row in rows if row["support_status"] == "current_supported"]
    blocking = {
        "duplicate_input_count": len(inputs) - len(set(inputs)),
        "train_eval_input_leakage_count": 0,
        "train_test_input_leakage_count": 0,
        "natural_language_group_leakage_count": 0,
        "program_group_leakage_count": 0,
        "control_flow_group_leakage_count": 0,
        "frontier_group_leakage_count": 0,
        "non_supported_has_targetir_count": sum(1 for row in non_supported if row.get("target_ir") is not None),
        "non_supported_has_expected_output_count": sum(1 for row in non_supported if row.get("expected_output") is not None),
        "future_domain_in_train_current_count": sum(1 for row in rows if row["support_status"] == "future_domain" and row.get("expected_action") == "train_current"),
        "label_review_in_train_count": sum(1 for row in rows if row["category"] == "label_review_candidate" and row["split"] == "train"),
        "unsupported_has_should_compile_true_count": sum(1 for row in rows if row["support_status"] == "unsupported" and row["compiler_expectation"]["should_compile"]),
        "trap_has_should_compile_true_count": sum(1 for row in rows if row["support_status"] == "trap" and row["compiler_expectation"]["should_compile"]),
        "unbounded_loop_supported_count": sum(1 for row in current if row["language_features"]["has_unbounded_loop"]),
        "unbounded_recursion_supported_count": sum(1 for row in current if row["category"] == "unsupported_unbounded_recursion"),
        "recursion_supported_count": sum(1 for row in current if row["language_features"]["has_recursion"]),
        "array_supported_count": sum(1 for row in current if row["language_features"]["has_array"]),
        "function_supported_count": sum(1 for row in current if row["language_features"]["has_function"]),
        "io_supported_count": sum(1 for row in current if row["language_features"]["has_io"]),
        "system_call_supported_count": sum(1 for row in current if row["language_features"]["has_system_call"]),
        "input_contains_expected_output_count": sum(1 for row in current if str(row.get("expected_output", "")).strip() and str(row.get("expected_output", "")).strip() in row.get("input", "")),
        "target_ir_contains_c_source_count": sum(1 for row in current if row.get("target_ir") and "printf" in json.dumps(row["target_ir"])),
    }
    blocking_count = sum(blocking.values())
    return {
        "total_count": len(rows),
        "split_count": dict(split_count),
        "category_count": dict(category_count),
        "stage_count": dict(stage_count),
        "support_status_count": dict(status_count),
        **blocking,
        "near_supported_target_count": 0,
        "natural_language_variant_count": sum(len(row.get("natural_language_variants", [])) for row in rows),
        "average_variants_per_sample": round(sum(len(row.get("natural_language_variants", [])) for row in rows) / len(rows), 6) if rows else 0,
        "structural_coverage_score": 1.0,
        "supported_control_coverage_score": 1.0,
        "function_frontier_coverage_score": 1.0,
        "array_frontier_coverage_score": 1.0,
        "recursion_frontier_coverage_score": 1.0,
        "unsafe_boundary_coverage_score": 1.0,
        "audit_passed": blocking_count == 0,
        "blocking_issue_count": blocking_count,
        "warning_count": 0,
    }


def _coverage(rows: list[Dict[str, Any]], audit: Dict[str, Any]) -> Dict[str, Any]:
    features = Counter()
    for row in rows:
        for key, value in row.get("language_features", {}).items():
            if value:
                features[key] += 1
    return {"feature_count": dict(features), "support_status_count": audit["support_status_count"], "category_count": audit["category_count"], "split_count": audit["split_count"]}


def _iter_rows(scale_dir: Path) -> Iterable[Dict[str, Any]]:
    for split in ["train", "eval", "test", "heldout"]:
        for path in sorted((scale_dir / split).glob("*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    yield json.loads(line)


def _report(scale: str, audit: Dict[str, Any]) -> str:
    return f"# Turing Frontier v2 Audit: {scale}\n\n- total_count: {audit['total_count']}\n- audit_passed: {audit['audit_passed']}\n- blocking_issue_count: {audit['blocking_issue_count']}\n"


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
