from __future__ import annotations

from typing import Any, Dict


def build_capability_balance_report(dashboard: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "capability_balance_report_completed": True,
        "capability_balance_score": dashboard["capability_balance_score"],
        "old_strong_stage_preserved": dashboard["old_strong_stage_delta"] >= -0.01,
        "boundary_preserved": dashboard["boundary_false_accept_delta"] == 0.0,
        "future_domain_preserved": dashboard["future_false_accept_delta"] == 0.0,
        "language_domain_preserved": dashboard["english_mixed_accept_delta"] == 0.0,
        "function_array_recursion_isolation_preserved": dashboard["function_array_recursion_isolation_delta"] == 0.0,
        "report_passed": dashboard["dashboard_passed"],
    }
