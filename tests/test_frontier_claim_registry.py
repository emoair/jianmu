import json
from pathlib import Path

from jianmu.self_learning.darwinforge.frontier_review_proof_readiness_rc_prep import ReviewInputs, run_v0_9_28


def test_frontier_claim_registry_blocks_overclaims(tmp_path: Path) -> None:
    run_v0_9_28(ReviewInputs(Path("records"), Path("records/v0_9_26_1"), Path("records/v0_9_27"), Path("records/v0_9_27_1"), tmp_path))
    payload = json.loads((tmp_path / "frontier_claim_registry.json").read_text(encoding="utf-8"))
    formal_claim = [claim for claim in payload["claims"] if claim["claim"] == "formal Turing completeness proven"][0]
    assert formal_claim["allowed"] is False
    assert "production readiness" in payload["forbidden_claims_blocked"]
