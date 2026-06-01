from __future__ import annotations

from jianmu.self_learning.darwinforge.redqueen_targeted_code_assignment import build_redqueen_targeted_code_assignment


def test_redqueen_targeted_code_assignment_required_features(tmp_path):
    result = build_redqueen_targeted_code_assignment(tmp_path)
    assignment = next(row for row in result["assignment_profiles"] if row["assignment_id"] == "loop_strengthening_assignment")
    assert assignment["required_features"]["has_for_loop"] is True
    assert assignment["safety_contract"]["no_runtime_gate"] is True
