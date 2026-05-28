from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.turing_frontier_grammar import FRONTIER_STAGES


def build_frontier_schedule() -> Dict[str, Any]:
    stages: List[Dict[str, Any]] = []
    for index, stage in enumerate(FRONTIER_STAGES, start=1):
        supported = stage in {
            "variable_declaration",
            "assignment_sequence",
            "multi_variable_sequence",
            "if_else_basic",
            "if_else_nested",
            "bounded_for_loop",
            "bounded_while_with_fuel",
            "nested_bounded_control",
            "bounded_control_hard_supported",
        }
        stages.append({
            "order": index,
            "stage_name": stage,
            "included_categories": ["current_supported_bounded_substrate", "bounded_control_hard_supported"] if supported else ["future_or_boundary"],
            "target_supported_ratio": 1.0 if supported else 0.0,
            "promotion_allowed": False,
            "real_promotion_allowed": False,
            "expected_exit_condition": "audit only; no Turing-completeness claim",
        })
    return {"dataset_version": "v0.9.9", "stages": stages}


def write_frontier_schedule(path: str | Path) -> Dict[str, Any]:
    schedule = build_frontier_schedule()
    Path(path).write_text(json.dumps(schedule, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return schedule

