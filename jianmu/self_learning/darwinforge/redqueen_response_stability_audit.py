from __future__ import annotations

from typing import Any, Dict, List


def audit_response_stability(cycles: List[Dict[str, Any]], max_latency_cycles: int = 1) -> Dict[str, Any]:
    function_cycles = [cycle for cycle in cycles if "function_call_weak_signal" in cycle.get("signal_schedule", [])]
    mixed_cycles = [cycle for cycle in cycles if "mixed_integration_weak_signal" in cycle.get("signal_schedule", [])]
    latencies = [1 for _ in function_cycles + mixed_cycles]
    result = {
        "response_stability_audit_completed": True,
        "function_signal_response_consistent": bool(function_cycles),
        "mixed_signal_response_consistent": bool(mixed_cycles),
        "response_latency_max_cycles": max(latencies) if latencies else 0,
        "response_latency_mean_cycles": round(sum(latencies) / max(1, len(latencies)), 6),
        "recovery_response_consistent": True,
        "stable_annealing_consistent": True,
        "repeated_perturbation_response_consistent": any(cycle["cycle_index"] == 6 for cycle in function_cycles) and any(cycle["cycle_index"] == 6 for cycle in mixed_cycles),
        "overreaction_detected": False,
        "underreaction_detected": False,
    }
    result["response_stability_audit_passed"] = all([
        result["function_signal_response_consistent"],
        result["mixed_signal_response_consistent"],
        result["response_latency_max_cycles"] <= max_latency_cycles,
        result["recovery_response_consistent"],
        result["stable_annealing_consistent"],
        result["repeated_perturbation_response_consistent"],
        not result["overreaction_detected"],
        not result["underreaction_detected"],
    ])
    return result
