from __future__ import annotations

from jianmu.self_learning.darwinforge.redqueen_autopsy import load_inputs
from jianmu.self_learning.darwinforge.redqueen_contrastive_pair_audit import audit_redqueen_contrastive_pairs
from jianmu.self_learning.darwinforge.redqueen_pattern_roi import compute_redqueen_pattern_roi
from jianmu.self_learning.darwinforge.redqueen_spec_attribution import compute_redqueen_spec_attribution


def test_contrastive_pair_audit_outputs_recommendations() -> None:
    data = load_inputs("records/v0_9_17", "records/v0_9_18", "records/v0_9_18_2", "datasets/v0_9_17_redqueen_curriculum")
    pattern = compute_redqueen_pattern_roi(data, compute_redqueen_spec_attribution(data))
    result = audit_redqueen_contrastive_pairs(data, pattern)
    assert result["recommended_contrast_pair_templates"]
    assert "contrast_pairs_are_underused" in result
