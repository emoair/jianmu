import json
from pathlib import Path

from jianmu.self_learning.darwinforge.frontier_review_proof_readiness_rc_prep import ReviewInputs, run_v0_9_28


def test_while_language_proof_review(tmp_path: Path) -> None:
    run_v0_9_28(ReviewInputs(Path("records"), Path("records/v0_9_26_1"), Path("records/v0_9_27"), Path("records/v0_9_27_1"), tmp_path))
    payload = json.loads((tmp_path / "proof_artifact_review" / "while_language_proof_review.json").read_text(encoding="utf-8"))
    assert payload["while_condition"]
    assert payload["zero_nonzero_condition"]
    assert payload["finite_validation_is_not_formal_proof"] is True
