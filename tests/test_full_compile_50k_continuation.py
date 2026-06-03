import json
from pathlib import Path

from jianmu.self_learning.darwinforge.frontier_review_proof_readiness_rc_prep import ReviewInputs, run_v0_9_28


def test_full_compile_50k_continuation_accounting(tmp_path: Path) -> None:
    run_v0_9_28(ReviewInputs(Path("records"), Path("records/v0_9_26_1"), Path("records/v0_9_27"), Path("records/v0_9_27_1"), tmp_path))
    payload = json.loads((tmp_path / "full_compile_50k_continuation.json").read_text(encoding="utf-8"))
    assert payload["previous_clean_invocations"] == 20000
    assert payload["new_continuation_invocations"] == 0
    assert payload["total_accounted_invocations"] == 20000
    assert payload["full_compile_50k_clean"] is False
    assert payload["continuation_partial"] is True
