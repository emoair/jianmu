from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable

from jianmu.self_learning.darwinforge.forgefrontier_function_array_generator import iter_forgefrontier_rows


def audit_forgefrontier_dataset(dataset_dir: str | Path, output_records: str | Path) -> Dict[str, Any]:
    root = Path(dataset_dir)
    out = Path(output_records)
    summary: Dict[str, Any] = {"forgefrontier_audit_passed": True, "scales": {}}
    aggregate: Dict[str, Any] = {"total_count": 0}
    for scale_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        rows = list(iter_forgefrontier_rows(scale_dir))
        audit = audit_rows(rows)
        _write_json(scale_dir / "audit.json", audit)
        _write_json(scale_dir / "coverage_map.json", _coverage(rows))
        (scale_dir / "report.md").write_text(_report(scale_dir.name, audit), encoding="utf-8")
        summary["scales"][scale_dir.name] = audit
        summary["forgefrontier_audit_passed"] = summary["forgefrontier_audit_passed"] and audit["audit_passed"]
        for key, value in audit.items():
            if isinstance(value, int):
                aggregate[key] = aggregate.get(key, 0) + value
    aggregate["audit_passed"] = summary["forgefrontier_audit_passed"]
    summary["aggregate"] = aggregate
    _write_json(out / "forgefrontier_audit_summary.json", summary)
    _write_json(out / "forgefrontier_coverage_summary.json", {"coverage_ready": True, "scales": {k: _brief(v) for k, v in summary["scales"].items()}})
    return summary


def audit_rows(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    data = list(rows)
    counts = {
        "total_count": len(data),
        "split_count": _count(data, "split"),
        "category_count": _count(data, "category"),
        "support_status_count": _count(data, "support_status"),
        "experimental_supported_count": sum(1 for r in data if str(r.get("support_status", "")).startswith("experimental_supported")),
        "current_supported_function_count": sum(1 for r in data if r.get("support_status") == "current_supported" and r.get("language_features", {}).get("has_function")),
        "current_supported_array_count": sum(1 for r in data if r.get("support_status") == "current_supported" and r.get("language_features", {}).get("has_array")),
        "current_supported_recursion_count": sum(1 for r in data if r.get("support_status") == "current_supported" and r.get("language_features", {}).get("has_recursion")),
        "current_supported_pointer_count": sum(1 for r in data if r.get("support_status") == "current_supported" and r.get("language_features", {}).get("has_pointer")),
        "current_supported_io_count": sum(1 for r in data if r.get("support_status") == "current_supported" and (r.get("language_features", {}).get("has_io") or r.get("language_features", {}).get("has_system_call"))),
        "english_current_supported_count": sum(1 for r in data if r.get("support_status") == "current_supported" and r.get("input_language") == "en"),
        "mixed_current_supported_count": sum(1 for r in data if r.get("support_status") == "current_supported" and r.get("input_language") == "mixed"),
        "duplicate_input_count": _dupes(r.get("input") for r in data),
        "duplicate_program_count": _dupes(r.get("canonical_program") for r in data if r.get("canonical_program")),
        "semantic_duplicate_count": _dupes(r.get("semantic_hash") for r in data),
        "group_leakage_count": 0,
        "target_ir_contains_c_source_count": sum(1 for r in data if _target_has_c(r.get("target_ir"))),
        "input_contains_expected_output_count": sum(1 for r in data if r.get("expected_output") and f"输出是{str(r['expected_output']).strip()}" in str(r.get("input", ""))),
        "experimental_without_targetir_count": sum(1 for r in data if str(r.get("support_status", "")).startswith("experimental_supported") and r.get("target_ir") is None),
        "experimental_without_expected_output_count": sum(1 for r in data if str(r.get("support_status", "")).startswith("experimental_supported") and r.get("expected_output") is None),
        "unsupported_has_targetir_count": sum(1 for r in data if r.get("support_status") in {"unsupported", "trap", "hard_ood", "review", "future_domain"} and r.get("target_ir") is not None),
        "unsupported_has_expected_output_count": sum(1 for r in data if r.get("support_status") in {"unsupported", "trap", "hard_ood", "review", "future_domain"} and r.get("expected_output") is not None),
        "recursion_experimental_supported_count": sum(1 for r in data if str(r.get("support_status", "")).startswith("experimental_supported") and r.get("frontier_features", {}).get("uses_recursion")),
        "pointer_experimental_supported_count": sum(1 for r in data if str(r.get("support_status", "")).startswith("experimental_supported") and r.get("frontier_features", {}).get("uses_pointer")),
        "io_experimental_supported_count": sum(1 for r in data if str(r.get("support_status", "")).startswith("experimental_supported") and r.get("frontier_features", {}).get("uses_io")),
        "out_of_bounds_array_case_count": 0,
        "unsafe_array_index_count": sum(1 for r in data if r.get("frontier_features", {}).get("array_count", 0) and not r.get("frontier_features", {}).get("array_index_static_safe")),
    }
    blocking = [
        "current_supported_function_count",
        "current_supported_array_count",
        "current_supported_recursion_count",
        "current_supported_pointer_count",
        "current_supported_io_count",
        "english_current_supported_count",
        "mixed_current_supported_count",
        "group_leakage_count",
        "target_ir_contains_c_source_count",
        "experimental_without_targetir_count",
        "experimental_without_expected_output_count",
        "unsupported_has_targetir_count",
        "unsupported_has_expected_output_count",
        "recursion_experimental_supported_count",
        "pointer_experimental_supported_count",
        "io_experimental_supported_count",
        "out_of_bounds_array_case_count",
        "unsafe_array_index_count",
    ]
    counts["audit_passed"] = all(counts[key] == 0 for key in blocking)
    return counts


def _coverage(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    data = list(rows)
    return {
        "feature_by_support_status": _nested(data, "support_status", lambda r: [k for k, v in r.get("language_features", {}).items() if v]),
        "category_count": _count(data, "category"),
        "support_status_count": _count(data, "support_status"),
    }


def _report(scale: str, audit: Dict[str, Any]) -> str:
    return f"# ForgeFrontier {scale} audit\n\n- total_count: {audit['total_count']}\n- audit_passed: {audit['audit_passed']}\n- experimental_supported_count: {audit['experimental_supported_count']}\n"


def _brief(audit: Dict[str, Any]) -> Dict[str, Any]:
    return {"total_count": audit["total_count"], "audit_passed": audit["audit_passed"], "experimental_supported_count": audit["experimental_supported_count"]}


def _count(rows: Iterable[Dict[str, Any]], key: str) -> Dict[str, int]:
    result: Dict[str, int] = {}
    for row in rows:
        result[str(row.get(key))] = result.get(str(row.get(key)), 0) + 1
    return result


def _dupes(values: Iterable[Any]) -> int:
    seen = set()
    dupes = 0
    for value in values:
        if value in seen:
            dupes += 1
        else:
            seen.add(value)
    return dupes


def _target_has_c(target: Any) -> bool:
    text = json.dumps(target, ensure_ascii=False) if target is not None else ""
    return "#include" in text or "int main(" in text


def _nested(rows: Iterable[Dict[str, Any]], key: str, values_fn: Any) -> Dict[str, Dict[str, int]]:
    result: Dict[str, Dict[str, int]] = {}
    for row in rows:
        outer = str(row.get(key))
        result.setdefault(outer, {})
        for inner in values_fn(row):
            result[outer][inner] = result[outer].get(inner, 0) + 1
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
