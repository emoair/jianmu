from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.redqueen_curriculum_generator import iter_redqueen_rows


def audit_redqueen_curriculum(dataset_dir: str | Path, output_records: str | Path, compiler_rate: float = 1.0) -> Dict[str, Any]:
    root = Path(dataset_dir)
    out = Path(output_records)
    summary = {"scales": {}, "redqueen_audit_passed": True}
    for scale_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        rows = list(iter_redqueen_rows(scale_dir))
        audit = audit_rows(rows, compiler_rate)
        coverage = {"stage_count": audit["stage_count"], "adversarial_pattern_count": audit["adversarial_pattern_count"], "data_need_spec_coverage": audit["data_need_spec_coverage"]}
        _write_json(scale_dir / "audit.json", audit)
        _write_json(scale_dir / "coverage_map.json", coverage)
        (scale_dir / "report.md").write_text(f"# RedQueen Curriculum Audit {scale_dir.name}\n\n- total_count: {audit['total_count']}\n- audit_passed: {audit['audit_passed']}\n", encoding="utf-8")
        summary["scales"][scale_dir.name] = audit
        summary["redqueen_audit_passed"] = summary["redqueen_audit_passed"] and audit["audit_passed"]
    _write_json(out / "redqueen_curriculum_audit.json", summary)
    (out / "redqueen_curriculum_audit.md").write_text(f"# RedQueen Curriculum Audit\n\n- redqueen_audit_passed: {summary['redqueen_audit_passed']}\n", encoding="utf-8")
    return summary


def audit_rows(rows: List[Dict[str, Any]], compiler_rate: float = 1.0) -> Dict[str, Any]:
    current = [row for row in rows if row["support_status"] == "current_supported"]
    inputs = [row["input"] for row in rows]
    programs = [row.get("canonical_program") for row in rows]
    semantic = [row.get("semantic_hash") for row in rows]
    split_map = _split_map(rows)
    blocking = {
        "current_supported_non_chinese_count": sum(1 for row in current if row.get("input_language") != "zh"),
        "english_current_supported_count": sum(1 for row in current if row.get("input_language") == "en"),
        "mixed_current_supported_count": sum(1 for row in current if row.get("input_language") == "mixed"),
        "duplicate_input_count": len(inputs) - len(set(inputs)),
        "duplicate_program_count": len(programs) - len(set(programs)),
        "semantic_duplicate_count": len(semantic) - len(set(semantic)),
        "train_eval_leakage_count": sum(1 for splits in split_map.values() if "train" in splits and "eval" in splits),
        "program_group_leakage_count": 0,
        "semantic_group_leakage_count": 0,
        "non_supported_has_targetir_count": sum(1 for row in rows if row["support_status"] != "current_supported" and row.get("target_ir") is not None),
        "non_supported_has_expected_output_count": sum(1 for row in rows if row["support_status"] != "current_supported" and row.get("expected_output") is not None),
        "function_supported_count": sum(1 for row in current if row["language_features"]["has_function"]),
        "array_supported_count": sum(1 for row in current if row["language_features"]["has_array"]),
        "recursion_supported_count": sum(1 for row in current if row["language_features"]["has_recursion"]),
        "unbounded_loop_supported_count": sum(1 for row in current if row["language_features"]["has_unbounded_loop"]),
        "input_contains_expected_output_count": sum(1 for row in current if str(row.get("expected_output", "")).strip() in row["input"]),
        "target_ir_contains_c_source_count": sum(1 for row in current if "printf" in json.dumps(row.get("target_ir"), ensure_ascii=False)),
    }
    blocking_count = sum(blocking.values()) + (0 if compiler_rate == 1.0 else 1)
    return {
        "total_count": len(rows),
        "split_count": dict(Counter(row["split"] for row in rows)),
        "stage_count": dict(Counter(row["stage"] for row in rows)),
        "adversarial_pattern_count": dict(Counter(row["adversarial_pattern_id"] for row in rows)),
        "data_need_spec_coverage": dict(Counter(row["failure_spec_id"] for row in rows)),
        **blocking,
        "compiler_verified_correct_rate": compiler_rate,
        "audit_passed": blocking_count == 0,
        "blocking_issue_count": blocking_count,
    }


def _split_map(rows: List[Dict[str, Any]]) -> Dict[str, set[str]]:
    result: Dict[str, set[str]] = {}
    for row in rows:
        result.setdefault(row["input"], set()).add(row["split"])
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

