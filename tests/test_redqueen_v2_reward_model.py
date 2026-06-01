from __future__ import annotations

from jianmu.self_learning.darwinforge.redqueen_v2_reward_model import redqueen_v2_reward, reward_component_schema


def test_redqueen_v2_reward_model_uses_audit_penalties_not_runtime_gate() -> None:
    assert redqueen_v2_reward({"top1_gain": 1.0, "data_contract_violation_penalty": 1.0}) < 0
    assert "schema/audit/records" in reward_component_schema()["data_contract_violation_penalty"]
