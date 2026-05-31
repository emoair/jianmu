from __future__ import annotations

from jianmu.self_learning.darwinforge.redqueen_autopsy import load_inputs
from jianmu.self_learning.darwinforge.redqueen_pattern_roi import compute_redqueen_pattern_roi
from jianmu.self_learning.darwinforge.redqueen_spec_attribution import compute_redqueen_spec_attribution


def test_redqueen_pattern_roi_recommends_actions() -> None:
    data = load_inputs("records/v0_9_17", "records/v0_9_18", "records/v0_9_18_2", "datasets/v0_9_17_redqueen_curriculum")
    spec = compute_redqueen_spec_attribution(data)
    result = compute_redqueen_pattern_roi(data, spec)
    actions = {row["recommended_action"] for row in result["patterns"]}
    assert actions
    assert result["top_positive_patterns"]
