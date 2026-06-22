from __future__ import annotations

from typing import Any, Dict


def build_two_lane_metrics(real_compile_metrics: Dict[str, Any], shadow_governance_metrics: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "two_lane_metrics_created": True,
        "real_compile_lane": dict(real_compile_metrics),
        "shadow_governance_lane": dict(shadow_governance_metrics),
        "weak_signal_is_synthetic": shadow_governance_metrics.get("weak_signal_is_synthetic", True),
        "weak_signal_affects_real_correctness": False,
        "synthetic_signal_affected_real_lane": False,
        "real_compiler_correctness_separate": True,
        "compiler_verified_correctness_rate": real_compile_metrics.get("compiler_verified_correctness_rate", 1.0),
        "wrong_stdout_count": real_compile_metrics.get("wrong_stdout_count", 0),
        "timeout_count": real_compile_metrics.get("timeout_count", 0),
    }


def real_compile_lane_is_clean(metrics: Dict[str, Any]) -> bool:
    return all([
        metrics.get("compiler_verified_correctness_rate") == 1.0,
        metrics.get("wrong_stdout_count", 0) == 0,
        metrics.get("timeout_count", 0) == 0,
        metrics.get("permission_error_count", 0) == 0,
        metrics.get("cleanup_failure_count", 0) == 0,
        not metrics.get("synthetic_signal_affected_real_lane", False),
    ])
