import json
from pathlib import Path

from jianmu.self_learning.darwinforge.frontier_review_proof_readiness_rc_prep import ReviewInputs, run_v0_9_28


def test_proof_boundary_notice(tmp_path: Path) -> None:
    run_v0_9_28(ReviewInputs(Path("records"), Path("records/v0_9_26_1"), Path("records/v0_9_27"), Path("records/v0_9_27_1"), tmp_path))
    payload = json.loads((tmp_path / "proof_artifact_review" / "proof_readiness.json").read_text(encoding="utf-8"))
    assert payload["constructive_mapping_documented"] is True
    assert payload["finite_validation_is_not_formal_proof"] is True
    assert payload["formal_turing_completeness_proven"] is False
