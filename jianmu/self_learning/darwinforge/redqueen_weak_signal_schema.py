from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from jianmu.self_learning.darwinforge.architecture_finalization_schema import PROFILE_NAME
from jianmu.self_learning.darwinforge.redqueen_real_landing_schema import STILL_NOT_PROVEN_REAL_LANDING


STILL_NOT_PROVEN_WEAK_SIGNAL: Tuple[str, ...] = tuple(dict.fromkeys(tuple(STILL_NOT_PROVEN_REAL_LANDING) + (
    "RedQueen autonomous governance completed",
)))


@dataclass(frozen=True)
class RedQueenWeakSignalConfig:
    profile_name: str = PROFILE_NAME
    wall_clock_min_hours: float = 6.0
    max_runtime_hours: float = 6.0
    hard_stop_hours: float = 6.5
    cycles: int = 5
    cycle_min_hours: float = 1.0
    total_events_target: int = 220_000
    minimum_total_events: int = 130_000
    minimum_real_compiler_invocations: int = 90_000
    workers: int = 16
    compiler_workers: int = 16
    trace_writer_mode: str = "sharded"
    temp_dir_mode: str = "per_sample"
    accounting_lock: bool = True
    idle_grace_seconds: int = 30
    require_plan_follow_rate: float = 0.95


def build_controlled_weak_signal_design() -> Dict[str, Any]:
    result = {
        "weak_signal_design_created": True,
        "two_lane_metrics_enabled": True,
        "real_compile_lane_enabled": True,
        "shadow_governance_lane_enabled": True,
        "weak_signal_is_synthetic": True,
        "weak_signal_affects_real_correctness": False,
        "weak_signal_affects_scheduling_only": True,
        "real_compiler_correctness_separate": True,
        "production_claim_impact": "none",
        "supported_weak_signal_categories": ["function", "mixed", "structured_recursion"],
    }
    result["weak_signal_design_passed"] = all([
        result["weak_signal_is_synthetic"],
        not result["weak_signal_affects_real_correctness"],
        result["weak_signal_affects_scheduling_only"],
        result["real_compiler_correctness_separate"],
        result["production_claim_impact"] == "none",
    ])
    return result


def build_weak_signal_scenarios() -> List[Dict[str, Any]]:
    must_not_claim = [
        "real compiler weakness detected",
        "real compiler weakness fixed",
        "production support completed",
        "autonomous governance completed",
    ]
    return [
        {
            "scenario_id": "function_call_weak_signal",
            "category": "function",
            "weak_signal_is_synthetic": True,
            "affects_real_compiler": False,
            "affects_real_correctness": False,
            "synthetic_success_rate": 0.965,
            "synthetic_wrong_stdout_rate": 0.0,
            "synthetic_timeout_rate": 0.0,
            "synthetic_coverage_gap": "medium",
            "intended_redqueen_response": [
                "increase_function_samples",
                "lower_function_difficulty_or_add_basic_cases",
                "increase_function_active_review",
                "increase_function_shape_diversity",
                "anneal_after_signal_removed",
            ],
            "must_not_claim": must_not_claim,
        },
        {
            "scenario_id": "mixed_integration_weak_signal",
            "category": "mixed",
            "weak_signal_is_synthetic": True,
            "affects_real_compiler": False,
            "affects_real_correctness": False,
            "synthetic_success_rate": 0.975,
            "synthetic_replay_drift_rate": 0.01,
            "synthetic_coverage_gap": "medium",
            "intended_redqueen_response": [
                "increase_mixed_review",
                "increase_replay_recheck",
                "increase_boundary_stress",
                "avoid_global_overreaction",
            ],
            "must_not_claim": must_not_claim,
        },
        {
            "scenario_id": "structured_recursion_stable_signal",
            "category": "structured_recursion",
            "weak_signal_is_synthetic": True,
            "affects_real_compiler": False,
            "affects_real_correctness": False,
            "synthetic_success_rate": 1.0,
            "synthetic_wrong_stdout_rate": 0.0,
            "synthetic_timeout_rate": 0.0,
            "repeated_shape_risk": "low",
            "intended_redqueen_response": [
                "do_not_fabricate_recursion_weakness",
                "increase_recursion_difficulty_or_frontier",
                "preserve_recursion_minimum_review",
            ],
            "must_not_claim": must_not_claim,
        },
    ]


def build_multiround_config_record(config: RedQueenWeakSignalConfig) -> Dict[str, Any]:
    return {
        "wall_clock_min_hours": config.wall_clock_min_hours,
        "cycles": config.cycles,
        "total_events_target": config.total_events_target,
        "minimum_total_events": config.minimum_total_events,
        "minimum_real_compiler_invocations": config.minimum_real_compiler_invocations,
        "weak_signal_schedule": {
            "cycle_0": [],
            "cycle_1": ["function_call_weak_signal"],
            "cycle_2": ["function_call_weak_signal", "mixed_integration_weak_signal"],
            "cycle_3": ["mixed_integration_weak_signal"],
            "cycle_4": [],
        },
        "workers": config.workers,
        "compiler_workers": config.compiler_workers,
        "trace_writer_mode": config.trace_writer_mode,
        "temp_dir_mode": config.temp_dir_mode,
        "accounting_lock": config.accounting_lock,
    }
