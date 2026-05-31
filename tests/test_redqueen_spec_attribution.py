from __future__ import annotations

from jianmu.self_learning.darwinforge.redqueen_autopsy import load_inputs
from jianmu.self_learning.darwinforge.redqueen_spec_attribution import compute_redqueen_spec_attribution


def test_redqueen_spec_attribution_outputs_roi() -> None:
    data = load_inputs("records/v0_9_17", "records/v0_9_18", "records/v0_9_18_2", "datasets/v0_9_17_redqueen_curriculum")
    result = compute_redqueen_spec_attribution(data)
    assert len(result["specs"]) == 8
    assert all("roi_score" in row for row in result["specs"])
    assert result["measurement_status"] == "estimated"
