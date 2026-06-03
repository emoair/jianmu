from pathlib import Path

from jianmu.self_learning.darwinforge.turing_frontier_proof_witness_suite import generate_witness_suite


def test_witness_suite_metrics(tmp_path):
    result = generate_witness_suite(tmp_path)
    root = Path(result["artifact_path"])
    assert (root / "witness_suite_metrics.json").exists()
    assert result["witness_suite_completed"] is True
