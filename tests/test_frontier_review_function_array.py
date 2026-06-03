import json
from pathlib import Path

from jianmu.self_learning.darwinforge.frontier_review_proof_readiness_rc_prep import ReviewInputs, run_v0_9_28


def test_function_array_frontier_review(tmp_path: Path) -> None:
    run_v0_9_28(ReviewInputs(Path("records"), Path("records/v0_9_26_1"), Path("records/v0_9_27"), Path("records/v0_9_27_1"), tmp_path))
    payload = json.loads((tmp_path / "function_array_frontier_review.json").read_text(encoding="utf-8"))
    assert payload["review_ready"] is True
    assert payload["function_array_in_current_supported_count"] == 0
    assert payload["production_support_claimed"] is False
