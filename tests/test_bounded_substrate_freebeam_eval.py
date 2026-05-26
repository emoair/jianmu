from __future__ import annotations

from jianmu.self_learning.darwinforge.bounded_substrate_freebeam_eval import evaluate_freebeam
from jianmu.self_learning.darwinforge.bounded_substrate_training_state import BoundedSubstrateTrainingState


def test_bounded_substrate_training_does_not_read_target_fields_in_free_eval() -> None:
    row = {"id": "x", "category": "current_supported_turing_substrate", "stage": "variable_declaration", "input": "safe", "canonical_program": "long long x = 1;", "language_features": {}, "complexity": {}, "target_ir": {"secret": True}, "expected_output": "1\n"}
    result = evaluate_freebeam([row], BoundedSubstrateTrainingState(), "test", after_training=True)
    assert result["forbidden_field_access_count"] == 0


def test_bounded_substrate_freebeam_eval_forbidden_fields() -> None:
    result = evaluate_freebeam([], BoundedSubstrateTrainingState(), "empty")
    assert result["forbidden_field_access_count"] == 0
