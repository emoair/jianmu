from __future__ import annotations

from jianmu.self_learning.darwinforge.billion_state_access_audit import audit_billion_state_access
from jianmu.self_learning.darwinforge.billion_state_eval import analyze_billion_state_scaling


def test_billion_state_eval_does_not_claim_emergence_proven(tmp_path) -> None:
    access = audit_billion_state_access(tmp_path, [])
    result = analyze_billion_state_scaling(tmp_path, [], access)
    assert result["emergence_proven"] is False

