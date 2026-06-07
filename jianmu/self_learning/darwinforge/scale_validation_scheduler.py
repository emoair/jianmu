from __future__ import annotations

from typing import Any, Dict


def should_run_phase_b(reaudit: Dict[str, Any]) -> Dict[str, Any]:
    if not reaudit.get("phase_a_passed"):
        return {
            "phase_b_allowed": False,
            "reason": "phase_a_failed",
            "blocking_issues": ["phase_a_failed"] + list(reaudit.get("phase_a_blocking_issues", [])),
        }
    return {"phase_b_allowed": True, "reason": "phase_a_passed", "blocking_issues": []}

