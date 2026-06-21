from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.redqueen_adaptive_curriculum_executor import apply_adaptive_curriculum


def update_cycle_plan(cycle_dir: str | Path, current_plan: Dict[str, Any], post_metrics: Dict[str, Any], cycle_index: int) -> Dict[str, Any]:
    next_plan = apply_adaptive_curriculum(current_plan, post_metrics, cycle_index)
    path = Path(cycle_dir) / "cycle_next_plan.json"
    path.write_text(json.dumps(next_plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return next_plan
