from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

from jianmu.self_learning.darwinforge.arithmetic_training_runner import MODE_LIMITS, _mode_rows


def audit_arithmetic_leakage(records_dir: str | Path, dataset_dir: str | Path, output_dir: str | Path) -> Dict[str, Any]:
    records = Path(records_dir)
    dataset = Path(dataset_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    metrics = _load_json(records / "arithmetic_training_metrics.json")
    access = _source_access_audit()
    group = _heldout_group_audit(dataset)
    payload = {
        "leakage_audit_passed": (
            metrics.get("forbidden_field_access_count") == 0
            and not access["target_ir_access_before_candidate_generation"]
            and not access["expected_output_access_before_candidate_generation"]
            and not access["boundary_label_access_in_free_eval"]
            and group["heldout_train_group_leakage_count"] == 0
            and not group["input_contains_expected_output"]
        ),
        "forbidden_field_access_count": metrics.get("forbidden_field_access_count"),
        **access,
        **group,
    }
    _write_json(out / "leakage_audit.json", payload)
    (out / "leakage_audit.md").write_text(_md(payload), encoding="utf-8")
    return payload


def _source_access_audit() -> Dict[str, bool]:
    source = Path("jianmu/self_learning/darwinforge/arithmetic_freebeam_eval.py").read_text(encoding="utf-8")
    eval_body = source.split("def evaluate_arithmetic_freebeam", 1)[1]
    before_scoring = eval_body.split("# Post-generation scoring may inspect expected_output.", 1)[0]
    candidate_section = before_scoring.split("view = allowed_view(row)", 1)[-1]
    return {
        "target_ir_access_before_candidate_generation": "target_ir" in candidate_section,
        "expected_output_access_before_candidate_generation": "expected_output" in candidate_section,
        "boundary_label_access_in_free_eval": "boundary_label" in candidate_section,
        "expected_action_access_in_free_eval": "expected_action" in candidate_section,
        "nutrient_policy_access_in_free_eval": "nutrient_policy" in candidate_section,
        "toxicity_policy_access_in_free_eval": "toxicity_policy" in candidate_section,
    }


def _heldout_group_audit(dataset: Path) -> Dict[str, Any]:
    totals = {
        "heldout_train_input_leakage": 0,
        "heldout_train_expression_group_leakage": 0,
        "heldout_train_paraphrase_group_leakage": 0,
        "heldout_train_target_group_leakage": 0,
    }
    input_contains_expected = 0
    heldout_total = 0
    train_total = 0
    for mode in ["quick", "small", "medium", "large-light"]:
        cfg = MODE_LIMITS[mode]
        scale_dir = dataset / cfg["scale"]
        if not scale_dir.exists():
            continue
        train, _eval, _test, heldout = _mode_rows(scale_dir, cfg)
        train_total += len(train)
        heldout_total += len(heldout)
        totals["heldout_train_input_leakage"] += _intersection_count(train, heldout, "input")
        totals["heldout_train_expression_group_leakage"] += _intersection_count(train, heldout, "expression_group_id")
        totals["heldout_train_paraphrase_group_leakage"] += _intersection_count(train, heldout, "paraphrase_group_id")
        totals["heldout_train_target_group_leakage"] += _intersection_count(train, heldout, "target_group_id")
        input_contains_expected += sum(1 for row in heldout if _input_leaks_expected_output(row))
    return {
        **totals,
        "heldout_train_group_leakage_count": sum(totals.values()),
        "input_contains_expected_output": input_contains_expected > 0,
        "input_contains_expected_output_count": input_contains_expected,
        "heldout_rows_audited": heldout_total,
        "train_rows_audited": train_total,
    }


def _intersection_count(left: Iterable[Dict[str, Any]], right: Iterable[Dict[str, Any]], key: str) -> int:
    left_values = {row.get(key) for row in left if row.get(key) not in {None, ""}}
    right_values = {row.get(key) for row in right if row.get(key) not in {None, ""}}
    return len(left_values & right_values)


def _input_leaks_expected_output(row: Dict[str, Any]) -> bool:
    expected = str(row.get("expected_output") or "").strip()
    if not expected:
        return False
    text = str(row.get("input") or "").lower()
    escaped = re.escape(expected.lower())
    leak_patterns = [
        rf"(?:answer|output|result)\s*(?:is|=|:)?\s*{escaped}\b",
        rf"=\s*{escaped}\b",
    ]
    return any(re.search(pattern, text) for pattern in leak_patterns)


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _md(payload: Dict[str, Any]) -> str:
    return "\n".join([
        "# v0.9.3 Arithmetic Leakage Audit",
        "",
        f"- leakage_audit_passed: {payload['leakage_audit_passed']}",
        f"- forbidden_field_access_count: {payload['forbidden_field_access_count']}",
        f"- target_ir_access_before_candidate_generation: {payload['target_ir_access_before_candidate_generation']}",
        f"- expected_output_access_before_candidate_generation: {payload['expected_output_access_before_candidate_generation']}",
        f"- heldout_train_group_leakage_count: {payload['heldout_train_group_leakage_count']}",
        f"- input_contains_expected_output_count: {payload['input_contains_expected_output_count']}",
    ]) + "\n"


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
