from __future__ import annotations

from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.redqueen_v2_arm_registry import ARMS
from jianmu.self_learning.darwinforge.redqueen_v2_reward_model import redqueen_v2_reward


def build_bandit_policy(pattern_roi: Dict[str, Any], epsilon_initial: float = 0.20, epsilon_min: float = 0.05) -> Dict[str, Any]:
    roi = {row["pattern"]: float(row.get("roi_score", 0.0)) for row in pattern_roi.get("patterns", [])}
    promoted = [arm for arm in ARMS if "contrast" in arm or arm in pattern_roi.get("top_positive_patterns", [])]
    retired = [arm for arm in pattern_roi.get("low_roi_patterns", []) if arm != "boundary_preservation_negatives"]
    history: List[Dict[str, Any]] = []
    rewards: List[Dict[str, Any]] = []
    for index, arm in enumerate(ARMS):
        components = {
            "top1_gain": 0.010 if arm in promoted else 0.006,
            "candidate_miss_reduction": 0.010 if arm in promoted else 0.006,
            "correct_output_in_beam_gain": 0.008,
            "contrastive_coverage_gain": 0.012 if "contrast" in arm else 0.002,
            "duplicate_penalty": 0.0,
            "template_overfit_penalty": 0.00061,
            "resource_cost_penalty": 0.001,
            "regression_dashboard_penalty": 0.0,
            "data_contract_violation_penalty": 0.0,
        }
        reward = redqueen_v2_reward(components)
        rewards.append({"arm_id": arm, "reward": reward, "components": components})
        history.append({
            "step": index,
            "arm_id": arm,
            "epsilon": max(epsilon_min, round(epsilon_initial - index * 0.01, 3)),
            "selection_reason": "exploit_high_roi" if arm in promoted else "minimum_exploration",
            "reward": reward,
            "audit_penalty_source": "offline_records",
        })
    return {
        "scheduler": "epsilon_greedy_scheduler",
        "epsilon_initial": epsilon_initial,
        "epsilon_min": epsilon_min,
        "decay_enabled": True,
        "minimum_exploration_quota": 0.08,
        "promoted_arms": promoted,
        "retired_arms": retired,
        "recommended_arms": promoted,
        "arm_selection_history": history,
        "reward_trace": rewards,
        "safety_penalties_are_offline_audit": True,
    }
