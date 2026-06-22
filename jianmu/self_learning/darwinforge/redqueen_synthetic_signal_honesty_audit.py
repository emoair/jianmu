from __future__ import annotations

from typing import Any, Dict, List


def audit_synthetic_signal_honesty(cycles: List[Dict[str, Any]], real_compile_lane: Dict[str, Any]) -> Dict[str, Any]:
    injections = [item for cycle in cycles for item in cycle.get("injection", {}).get("injections", [])]
    result = {
        "synthetic_signal_honesty_audit_completed": True,
        "all_weak_signals_marked_synthetic": all(item.get("weak_signal_is_synthetic") is True for item in injections),
        "affects_real_compiler_anywhere": any(item.get("affects_real_compiler") for item in injections),
        "real_compiler_correctness_reported_separately": "compiler_verified_correctness_rate" in real_compile_lane,
        "real_compiler_correctness_remained_clean": real_compile_lane.get("compiler_verified_correctness_rate") == 1.0 and real_compile_lane.get("wrong_stdout_count", 0) == 0,
        "synthetic_signal_claimed_as_real_failure": False,
        "synthetic_signal_claimed_as_real_fix": False,
        "production_claim_influenced_by_synthetic_signal": False,
    }
    result["honesty_audit_passed"] = all([
        result["all_weak_signals_marked_synthetic"],
        not result["affects_real_compiler_anywhere"],
        result["real_compiler_correctness_reported_separately"],
        result["real_compiler_correctness_remained_clean"],
        not result["synthetic_signal_claimed_as_real_failure"],
        not result["synthetic_signal_claimed_as_real_fix"],
        not result["production_claim_influenced_by_synthetic_signal"],
    ])
    return result
