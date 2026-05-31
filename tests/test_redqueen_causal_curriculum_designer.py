from __future__ import annotations

from jianmu.self_learning.darwinforge.redqueen_autopsy import load_inputs
from jianmu.self_learning.darwinforge.redqueen_causal_curriculum_designer import design_redqueen_causal_curriculum
from jianmu.self_learning.darwinforge.redqueen_contrastive_pair_audit import audit_redqueen_contrastive_pairs
from jianmu.self_learning.darwinforge.redqueen_pattern_roi import compute_redqueen_pattern_roi
from jianmu.self_learning.darwinforge.redqueen_regression_sentinel import run_redqueen_regression_sentinel
from jianmu.self_learning.darwinforge.redqueen_spec_attribution import compute_redqueen_spec_attribution


def test_causal_curriculum_designer_outputs_plan() -> None:
    data = load_inputs("records/v0_9_17", "records/v0_9_18", "records/v0_9_18_2", "datasets/v0_9_17_redqueen_curriculum")
    pattern = compute_redqueen_pattern_roi(data, compute_redqueen_spec_attribution(data))
    contrast = audit_redqueen_contrastive_pairs(data, pattern)
    plan = design_redqueen_causal_curriculum(pattern, contrast, run_redqueen_regression_sentinel(data))
    assert plan["plan_name"] == "redqueen_v2_causal_curriculum"
    assert plan["recommended_contrast_pair_ratio"] > 0
