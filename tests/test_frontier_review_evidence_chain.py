from pathlib import Path

from jianmu.self_learning.darwinforge.frontier_review_proof_readiness_rc_prep import ReviewInputs, run_v0_9_28


def _inputs(tmp_path: Path) -> ReviewInputs:
    return ReviewInputs(
        records_root=Path("records"),
        source_records_v26_1=Path("records/v0_9_26_1"),
        source_records_v27=Path("records/v0_9_27"),
        source_records_v27_1=Path("records/v0_9_27_1"),
        output_records=tmp_path,
    )


def test_frontier_evidence_chain(tmp_path: Path) -> None:
    run_v0_9_28(_inputs(tmp_path))
    payload = (tmp_path / "frontier_evidence_chain.json").read_text(encoding="utf-8")
    assert '"evidence_chain_completed": true' in payload
    assert '"evidence_chain_clean": true' in payload
