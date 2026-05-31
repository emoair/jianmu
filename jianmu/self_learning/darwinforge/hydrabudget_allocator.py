from __future__ import annotations

from typing import Any, Dict, List


def allocate_hydrabudget(layers: List[Dict[str, Any]], threshold: float = 0.75, multiplier: float = 1.5) -> Dict[str, Any]:
    decisions = []
    for row in layers:
        allowed = (
            row["utilization_ratio"] >= threshold
            and row["candidate_miss_contribution"] >= 0.04
            and row["top1_gain_contribution"] > 0
            and row["boundary_risk_score"] == 0
            and row["future_risk_score"] == 0
            and row["layer_name"] not in {"trunk_global_routing", "major_branch_language_family"}
        )
        new_budget = min(1_000_000_000, int(row["current_budget_units"] * multiplier)) if allowed else row["current_budget_units"]
        decisions.append({"layer_name": row["layer_name"], "expand": allowed, "old_budget_units": row["current_budget_units"], "new_budget_units": new_budget, "multiplier": multiplier if allowed else 1.0})
    return {"threshold": threshold, "multiplier": multiplier, "decisions": decisions, "expansion_count": sum(1 for item in decisions if item["expand"])}

