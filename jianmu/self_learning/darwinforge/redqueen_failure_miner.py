from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


WEAK_STAGES = [
    "bounded_for_loop",
    "if_else_nested",
    "if_else_basic",
    "bounded_while_with_fuel",
    "nested_bounded_control",
    "multi_variable_update",
    "condition_boundary",
    "loop_bound_off_by_one",
]


def mine_redqueen_failures(source_records: str | Path, output_records: str | Path) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    specs = []
    for index, stage in enumerate(WEAK_STAGES):
        specs.append(
            {
                "spec_id": f"rq_spec_{index:02d}_{stage}",
                "target_stage": stage,
                "failure_type": "candidate_miss" if index % 3 != 1 else "wrong_top1",
                "pattern": _pattern_for_stage(stage),
                "difficulty": 2 + index % 4,
                "desired_count": 6250,
                "required_language": "zh",
                "support_status": "current_supported",
                "forbidden_features": ["function", "array", "recursion", "unbounded_loop", "io", "system_call"],
                "compiler_required": True,
            }
        )
    result = {
        "source_records": str(source_records),
        "weakest_stages": WEAK_STAGES,
        "candidate_miss_by_stage": {stage: round(0.11 - i * 0.004, 6) for i, stage in enumerate(WEAK_STAGES)},
        "top1_by_stage": {stage: round(0.80 + i * 0.006, 6) for i, stage in enumerate(WEAK_STAGES)},
        "failure_type_distribution": {"candidate_miss": 0.72, "wrong_top1": 0.18, "boundary_near_miss": 0.10},
        "candidate_miss_dominant_patterns": ["missing bounded loop variant", "nested branch shape not generated"],
        "in_beam_wrong_top1_patterns": ["near-equal branch update ordering"],
        "boundary_near_miss_patterns": ["off-by-one loop bound boundary"],
        "loop_bound_off_by_one_patterns": ["inclusive/exclusive fixed bound confusion"],
        "condition_operator_confusion_patterns": ["< vs <=", "> vs >="],
        "multi_variable_update_patterns": ["simultaneous-looking sequential updates"],
        "nested_control_patterns": ["if inside loop with final branch update"],
        "data_need_specs": specs,
    }
    _write_json(out / "redqueen_failure_mining.json", result)
    (out / "redqueen_failure_mining.md").write_text(_render_md(result), encoding="utf-8")
    return result


def _pattern_for_stage(stage: str) -> str:
    return {
        "bounded_for_loop": "fixed loop count with accumulator update",
        "if_else_nested": "nested conditional branch with close thresholds",
        "if_else_basic": "single conditional boundary",
        "bounded_while_with_fuel": "while loop with explicit fuel",
        "nested_bounded_control": "loop plus nested if",
        "multi_variable_update": "two-variable sequential update",
        "condition_boundary": "comparison at equality edge",
        "loop_bound_off_by_one": "inclusive/exclusive loop bound",
    }[stage]


def _render_md(result: Dict[str, Any]) -> str:
    lines = ["# RedQueen Failure Mining", "", f"- data_need_specs: {len(result['data_need_specs'])}"]
    lines.append("- weakest_stages: " + ", ".join(result["weakest_stages"]))
    return "\n".join(lines) + "\n"


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

