import json
from pathlib import Path

from jianmu.self_learning.darwinforge.frontier_review_proof_readiness_rc_prep import ReviewInputs, run_v0_9_28


def test_readiness_release_false_without_human_review(tmp_path: Path) -> None:
    run_v0_9_28(ReviewInputs(Path("records"), Path("records/v0_9_26_1"), Path("records/v0_9_27"), Path("records/v0_9_27_1"), tmp_path))
    payload = json.loads((tmp_path / "frontier_review_readiness.json").read_text(encoding="utf-8"))
    assert payload["ready_for_v1_0_rc1_branch"] is True
    assert payload["ready_for_v1_0_release"] is False
    assert payload["recommended_claim_level"] == "frontier_review_ready_but_50k_partial"
