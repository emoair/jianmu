from __future__ import annotations

from typing import Any, Dict, List


def detect_level_accounting_mode(scaleup: Dict[str, Any]) -> Dict[str, Any]:
    levels = {row.get("level_name"): row for row in scaleup.get("levels", [])}
    gate = levels.get("gate_5k", {})
    main = levels.get("main_20k", {})
    extended = levels.get("extended_50k", {})
    gate_feeds_main = main.get("previous_invocations_used") == gate.get("completed_invocations")
    main_feeds_extended = extended.get("previous_invocations_used") == main.get("completed_invocations")
    detected = "cumulative" if gate_feeds_main and main_feeds_extended else "independent"
    return {
        "level_accounting_mode_detected": detected,
        "gate_5k_includes_previous_v0_9_18": gate.get("previous_invocations_used", 0) > 0,
        "main_20k_includes_gate_5k": gate_feeds_main,
        "extended_50k_includes_main_20k": main_feeds_extended,
        "level_chain": _chain(scaleup.get("levels", [])),
    }


def reconcile_effective_invocations(scaleup: Dict[str, Any], accounting: Dict[str, Any], mode: str) -> Dict[str, int]:
    levels = {row.get("level_name"): row for row in scaleup.get("levels", [])}
    total = int(accounting.get("total_accounted_invocation_count", scaleup.get("total_accounted_invocation_count", 0)))
    if mode == "cumulative":
        return {
            "gate_5k_effective_invocations": min(total, int(levels.get("gate_5k", {}).get("completed_invocations", 0))),
            "main_20k_effective_invocations": total,
            "extended_50k_effective_invocations": total,
        }
    return {
        "gate_5k_effective_invocations": int(levels.get("gate_5k", {}).get("completed_invocations", 0)),
        "main_20k_effective_invocations": int(levels.get("main_20k", {}).get("completed_invocations", 0)),
        "extended_50k_effective_invocations": int(levels.get("extended_50k", {}).get("completed_invocations", 0)),
    }


def _chain(levels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "level_name": row.get("level_name"),
            "previous_invocations_used": row.get("previous_invocations_used", 0),
            "completed_invocations": row.get("completed_invocations", 0),
            "target_total_invocations": row.get("target_total_invocations", 0),
        }
        for row in levels
    ]
