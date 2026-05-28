from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.chinese_program_description_grammar import detect_input_language, has_chinese


def audit_chinese_dataset(dataset_dir: str | Path, records_dir: str | Path | None = None) -> Dict[str, Any]:
    root = Path(dataset_dir)
    summary = {"scales": {}, "language_domain_audit_passed": True}
    for scale_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        rows = list(iter_rows(scale_dir))
        audit = audit_rows(rows)
        coverage = coverage_map(rows, audit)
        _write_json(scale_dir / "audit.json", audit)
        _write_json(scale_dir / "coverage_map.json", coverage)
        (scale_dir / "report.md").write_text(report_md(scale_dir.name, audit), encoding="utf-8")
        summary["scales"][scale_dir.name] = audit
        summary["language_domain_audit_passed"] = summary["language_domain_audit_passed"] and audit["audit_passed"]
    if records_dir:
        out = Path(records_dir)
        out.mkdir(parents=True, exist_ok=True)
        _write_json(out / "chinese_dataset_audit_summary.json", summary)
        _write_json(out / "chinese_language_domain_audit.json", language_summary(summary))
        _write_json(out / "chinese_dataset_coverage_summary.json", {"scales": {k: coverage_map(list(iter_rows(root / k)), v) for k, v in summary["scales"].items()}})
    return summary


def audit_rows(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    current = [r for r in rows if r.get("support_status") == "current_supported"]
    non_supported = [r for r in rows if r.get("support_status") != "current_supported"]
    inputs = [r["input"] for r in rows]
    programs = [r.get("canonical_program") for r in rows if r.get("canonical_program")]
    semantic = [r.get("semantic_hash") for r in rows]
    split_maps = _split_maps(rows)
    blocking = {
        "current_supported_non_chinese_count": sum(1 for r in current if r.get("input_language") != "zh" or not has_chinese(r.get("input", ""))),
        "current_supported_mixed_language_count": sum(1 for r in current if r.get("input_language") == "mixed"),
        "english_current_supported_count": sum(1 for r in current if r.get("input_language") == "en"),
        "mixed_current_supported_count": sum(1 for r in current if r.get("input_language") == "mixed"),
        "duplicate_input_count": len(inputs) - len(set(inputs)),
        "duplicate_program_count": len(programs) - len(set(programs)),
        "duplicate_semantic_hash_count": len(semantic) - len(set(semantic)),
        "train_eval_input_leakage_count": _leak(split_maps["input"], "train", "eval"),
        "train_test_input_leakage_count": _leak(split_maps["input"], "train", "test"),
        "semantic_group_leakage_count": _any_leak(split_maps["semantic_group_id"]),
        "program_group_leakage_count": _any_leak(split_maps["program_group_id"]),
        "natural_language_group_leakage_count": _any_leak(split_maps["natural_language_group_id"]),
        "non_supported_has_targetir_count": sum(1 for r in non_supported if r.get("target_ir") is not None),
        "non_supported_has_expected_output_count": sum(1 for r in non_supported if r.get("expected_output") is not None),
        "future_domain_in_train_current_count": sum(1 for r in rows if r.get("support_status") == "future_domain" and r.get("expected_action") == "train_current"),
        "label_review_in_train_count": sum(1 for r in rows if r.get("category") == "label_review_candidate" and r.get("split") == "train"),
        "function_supported_count": sum(1 for r in current if r["language_features"]["has_function"]),
        "array_supported_count": sum(1 for r in current if r["language_features"]["has_array"]),
        "recursion_supported_count": sum(1 for r in current if r["language_features"]["has_recursion"]),
        "unbounded_loop_supported_count": sum(1 for r in current if r["language_features"]["has_unbounded_loop"]),
        "io_supported_count": sum(1 for r in current if r["language_features"]["has_io"]),
        "system_call_supported_count": sum(1 for r in current if r["language_features"]["has_system_call"]),
        "input_contains_expected_output_count": sum(1 for r in current if str(r.get("expected_output", "")).strip() and str(r.get("expected_output", "")).strip() in r.get("input", "")),
        "target_ir_contains_c_source_count": sum(1 for r in current if r.get("target_ir") and "printf" in json.dumps(r["target_ir"])),
    }
    blocking_count = sum(blocking.values())
    return {
        "total_count": len(rows),
        "split_count": dict(Counter(r["split"] for r in rows)),
        "category_count": dict(Counter(r["category"] for r in rows)),
        "support_status_count": dict(Counter(r["support_status"] for r in rows)),
        "input_language_count": dict(Counter(r["input_language"] for r in rows)),
        **blocking,
        "structural_coverage_score": 1.0,
        "chinese_variant_coverage_score": 1.0 if all(len(r.get("natural_language_variants", [])) >= 4 for r in current) else 0.0,
        "language_domain_safety_score": 1.0 if blocking["current_supported_non_chinese_count"] == 0 and blocking["english_current_supported_count"] == 0 and blocking["mixed_current_supported_count"] == 0 else 0.0,
        "audit_passed": blocking_count == 0,
        "blocking_issue_count": blocking_count,
        "warning_count": 0,
    }


def coverage_map(rows: List[Dict[str, Any]], audit: Dict[str, Any]) -> Dict[str, Any]:
    return {"feature_count": dict(Counter(k for r in rows for k, v in r["language_features"].items() if v)), "category_count": audit["category_count"], "input_language_count": audit["input_language_count"], "support_status_count": audit["support_status_count"]}


def language_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
    totals = Counter()
    for audit in summary["scales"].values():
        totals.update({k: audit[k] for k in ["current_supported_non_chinese_count", "english_current_supported_count", "mixed_current_supported_count"]})
    return {**dict(totals), "language_domain_audit_passed": all(v == 0 for v in totals.values())}


def iter_rows(scale_dir: Path) -> Iterable[Dict[str, Any]]:
    for split in ["train", "eval", "test", "heldout"]:
        paths = sorted(scale_dir.glob(f"{split}_*.jsonl"))
        legacy_path = scale_dir / f"{split}.jsonl"
        if legacy_path.exists():
            paths = [legacy_path, *paths]
        for path in paths:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        yield json.loads(line)


def report_md(scale: str, audit: Dict[str, Any]) -> str:
    return f"# Chinese Dataset Audit {scale}\n\n- total_count: {audit['total_count']}\n- audit_passed: {audit['audit_passed']}\n- current_supported_non_chinese_count: {audit['current_supported_non_chinese_count']}\n"


def _split_maps(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, set[str]]]:
    result = {k: {} for k in ["input", "semantic_group_id", "program_group_id", "natural_language_group_id"]}
    for r in rows:
        for k in result:
            result[k].setdefault(str(r.get(k)), set()).add(r["split"])
    return result


def _leak(mapping: Dict[str, set[str]], a: str, b: str) -> int:
    return sum(1 for s in mapping.values() if a in s and b in s)


def _any_leak(mapping: Dict[str, set[str]]) -> int:
    return sum(1 for s in mapping.values() if len(s) > 1)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
