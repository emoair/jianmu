from dataclasses import replace

from jianmu.self_learning.darwinforge.controlled_opt_in_negative_validation import run_negative_boundary_validation
from jianmu.self_learning.darwinforge.controlled_opt_in_support_schema import ControlledOptInSupportConfig


def test_negative_validation_rejects_unknown_policy(tmp_path):
    result = run_negative_boundary_validation(tmp_path, ControlledOptInSupportConfig(negative_validation_events=12))
    assert result["unknown_policy_rejection_rate"] == 1.0
    assert result["unsafe_compile_invoked_count"] == 0


def test_negative_validation_blocks_without_opt_in(tmp_path):
    result = run_negative_boundary_validation(tmp_path, ControlledOptInSupportConfig(negative_validation_events=12))
    assert result["default_blocking_success_rate"] == 1.0
    assert result["bridge_reachable_without_opt_in_count"] == 0


def test_negative_validation_blocks_production_promotion(tmp_path):
    result = run_negative_boundary_validation(tmp_path, ControlledOptInSupportConfig(negative_validation_events=12))
    assert result["production_promotion_rejection_rate"] == 1.0
    assert result["real_promotion_enabled_count"] == 0
