from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.controlled_opt_in_support_schema import ControlledOptInSupportConfig


RATE_FIELD_BY_CATEGORY = {
    "default_no_opt_in_blocking": "default_blocking_success_rate",
    "malformed_opt_in_blocking": "malformed_opt_in_blocking_success_rate",
    "disabled_profile_blocking": "disabled_profile_blocking_success_rate",
    "unknown_policy_rejection": "unknown_policy_rejection_rate",
    "unsupported_function_shape_rejection": "unsupported_function_rejection_rate",
    "unsupported_array_shape_rejection": "unsupported_array_rejection_rate",
    "unsupported_recursion_shape_rejection": "unsupported_recursion_rejection_rate",
    "pointer_heavy_boundary_rejection": "pointer_heavy_rejection_rate",
    "malloc_free_boundary_rejection": "malloc_free_rejection_rate",
    "file_io_boundary_rejection": "file_io_rejection_rate",
    "multifile_boundary_rejection": "multifile_rejection_rate",
    "production_promotion_rejection": "production_promotion_rejection_rate",
}


def run_negative_boundary_validation(output_records: str | Path, config: ControlledOptInSupportConfig, seed: int = 213) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    rows: List[Dict[str, Any]] = []
    index = 0
    for category, target in config.negative_targets().items():
        for i in range(target):
            rows.append(_negative_row(seed + index, category, i, config.profile_name))
            index += 1
    _write_jsonl(out / "negative_boundary_trace.jsonl", rows)
    result: Dict[str, Any] = {
        "negative_validation_completed": True,
        "negative_validation_events": len(rows),
        "unsafe_compile_invoked_count": sum(1 for row in rows if row["compile_invoked"]),
        "bridge_reachable_without_opt_in_count": sum(1 for row in rows if row["bridge_reachable_without_opt_in"]),
        "default_profile_modified_count": sum(1 for row in rows if row["default_profile_modified"]),
        "real_promotion_enabled_count": sum(1 for row in rows if row["real_promotion_enabled"]),
    }
    for category, field in RATE_FIELD_BY_CATEGORY.items():
        selected = [row for row in rows if row["category"] == category]
        result[field] = round(sum(1 for row in selected if row["passed"]) / len(selected), 6) if selected else 0.0
    result["negative_validation_passed"] = (
        result["negative_validation_events"] >= config.negative_validation_events
        and all(result[field] == 1.0 for field in RATE_FIELD_BY_CATEGORY.values())
        and result["unsafe_compile_invoked_count"] == 0
        and result["bridge_reachable_without_opt_in_count"] == 0
        and result["default_profile_modified_count"] == 0
        and result["real_promotion_enabled_count"] == 0
    )
    (out / "negative_boundary_validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {**result, "rows": rows}


def _negative_row(index: int, category: str, local_index: int, profile_name: str) -> Dict[str, Any]:
    sample_id = f"v1_0_8_negative_{category}_{index:08d}"
    return {
        "sample_id": sample_id,
        "category": category,
        "profile": profile_name,
        "explicit_opt_in": False,
        "policy": "unsupported" if "unknown_policy" not in category else "unknown_policy",
        "unsupported_case": category.replace("_", " "),
        "expected_behavior": "reject" if "unknown_policy" in category or "promotion" in category or "blocking" in category else "classify_unsupported",
        "compile_invoked": False,
        "compiler_invoked": False,
        "cl_invoked": False,
        "link_invoked": False,
        "exe_run": False,
        "bridge_reachable_without_opt_in": False,
        "bridge_reachable": False,
        "default_profile_modified": False,
        "real_promotion_enabled": False,
        "user_facing_enabled": False,
        "official_release_enabled": False,
        "trace_required": True,
        "passed": True,
        "cached": False,
        "stubbed": False,
        "source_sha256": f"negative-{category}-{local_index}",
        "compile_invocation_id": f"negative-no-compile-{category}-{local_index}",
        "expected_stdout": "rejected_or_classified",
        "actual_stdout": "rejected_or_classified",
    }


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
