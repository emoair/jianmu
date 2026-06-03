import json
from pathlib import Path

from jianmu.self_learning.darwinforge.frontier_review_proof_readiness_rc_prep import ReviewInputs, run_v0_9_28


def test_rc1_preparation_bundle(tmp_path: Path) -> None:
    run_v0_9_28(ReviewInputs(Path("records"), Path("records/v0_9_26_1"), Path("records/v0_9_27"), Path("records/v0_9_27_1"), tmp_path))
    bundle = tmp_path / "v1_0_rc1_frontier_preparation_bundle"
    payload = json.loads((bundle / "rc1_branch_recommendation.json").read_text(encoding="utf-8"))
    assert payload["ready_for_v1_0_release"] is False
    assert payload["human_review_completed"] is False
    assert (bundle / "rc1_not_proven_notice.md").exists()
