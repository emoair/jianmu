from __future__ import annotations

from typing import Any, Dict


def audit_response_latency(response: Dict[str, Any], max_cycles: int = 1) -> Dict[str, Any]:
    result = {
        "response_latency_audit_completed": True,
        "function_response_latency_cycles": response.get("function_response_latency_cycles"),
        "mixed_response_latency_cycles": response.get("mixed_response_latency_cycles"),
    }
    result["response_latency_audit_passed"] = all([
        result["function_response_latency_cycles"] is not None,
        result["mixed_response_latency_cycles"] is not None,
        result["function_response_latency_cycles"] <= max_cycles,
        result["mixed_response_latency_cycles"] <= max_cycles,
    ])
    return result
