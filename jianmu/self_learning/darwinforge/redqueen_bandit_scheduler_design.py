from __future__ import annotations

from typing import Any, Dict

from jianmu.self_learning.darwinforge.redqueen_autopsy import build_bandit_diagnostic_simulation, build_bandit_scheduler_design


def design_redqueen_bandit_scheduler() -> Dict[str, Any]:
    return build_bandit_scheduler_design()


def simulate_redqueen_bandit_scheduler(pattern_roi: Dict[str, Any]) -> Dict[str, Any]:
    return build_bandit_diagnostic_simulation(pattern_roi)
