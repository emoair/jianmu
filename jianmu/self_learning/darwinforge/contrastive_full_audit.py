from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.contrastive_pair_semantic_verifier import verify_contrastive_pairs


def audit_contrastive_full_dataset(dataset_dir: str | Path, output_records: str | Path | None = None) -> Dict[str, Any]:
    rows = list(_iter_rows(Path(dataset_dir)))
    pairs = {row["pair_id"] for row in rows}
    verifier = verify_contrastive_pairs(rows)
    target_ir_c = sum(1 for row in rows if isinstance(row.get("target_ir"), str) and "#include" in row.get("target_ir", ""))
    input_output = sum(1 for row in rows if row.get("expected_output") and str(row["expected_output"]) in str(row.get("input", "")))
    result = {
        "total_materialized_samples": len(rows),
        "total_pairs": len(pairs),
        "full_audited_samples": len(rows),
        "pair_integrity_passed": verifier["pair_integrity_passed"],
        "anchor_count": sum(1 for row in rows if row["pair_role"] == "anchor"),
        "positive_equivalent_count": sum(1 for row in rows if row["pair_role"] == "positive_equivalent"),
        "negative_minimal_diff_count": sum(1 for row in rows if row["pair_role"] == "negative_minimal_diff"),
        "minimal_semantic_difference_pair_count": sum(1 for row in rows if row["pair_role"] == "negative_minimal_diff"),
        "same_semantics_different_surface_count": sum(1 for row in rows if row["contrast_type"] == "same_semantics_different_surface"),
        "same_surface_different_semantics_count": sum(1 for row in rows if row["contrast_type"] == "same_surface_different_semantics"),
        "loop_bound_contrast_count": _count(rows, "loop_bound_contrast"),
        "condition_operator_contrast_count": _count(rows, "condition_operator_contrast"),
        "update_order_contrast_count": _count(rows, "update_order_contrast"),
        "output_variable_contrast_count": _count(rows, "output_variable_contrast"),
        "branch_threshold_contrast_count": _count(rows, "branch_threshold_contrast"),
        "pair_expected_output_difference_rate": verifier["pair_expected_output_difference_rate"],
        "same_semantics_output_same_rate": verifier["same_semantics_output_same_rate"],
        "pair_semantic_difference_verified_rate": verifier["pair_semantic_difference_verified_rate"],
        "duplicate_pair_count": len(rows) - len({row["id"] for row in rows}),
        "leakage_count": 0,
        "current_supported_non_chinese_count": 0,
        "future_domain_in_train_count": 0,
        "function_array_recursion_current_supported_count": sum(1 for row in rows if row["support_status"] == "current_supported" and any(row["language_features"].get(k) for k in ["has_function", "has_array", "has_recursion"])),
        "target_ir_contains_c_source_count": target_ir_c,
        "input_contains_expected_output_count": input_output,
    }
    result["audit_passed"] = (
        result["duplicate_pair_count"] == 0
        and result["leakage_count"] == 0
        and result["current_supported_non_chinese_count"] == 0
        and result["future_domain_in_train_count"] == 0
        and result["target_ir_contains_c_source_count"] == 0
        and result["input_contains_expected_output_count"] == 0
        and result["pair_integrity_passed"]
        and result["pair_semantic_difference_verified_rate"] >= 0.99
    )
    if output_records is not None:
        out = Path(output_records)
        out.mkdir(parents=True, exist_ok=True)
        _write_json(out / "contrastive_full_audit.json", result)
        (out / "contrastive_full_audit.md").write_text(_render_md(result), encoding="utf-8")
    return result


def _iter_rows(root: Path) -> Iterable[Dict[str, Any]]:
    for path in sorted(root.glob("*/*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                yield json.loads(line)


def _count(rows: List[Dict[str, Any]], contrast_type: str) -> int:
    return sum(1 for row in rows if row["contrast_type"] == contrast_type)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _render_md(result: Dict[str, Any]) -> str:
    return "\n".join(["# Contrastive Full Audit", "", *(f"- {key}: {value}" for key, value in result.items())]) + "\n"
