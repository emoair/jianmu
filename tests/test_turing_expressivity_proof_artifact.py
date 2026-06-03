from pathlib import Path

from jianmu.self_learning.darwinforge.turing_expressivity_proof_artifact import generate_proof_artifact


def test_turing_expressivity_proof_artifact_generated(tmp_path):
    result = generate_proof_artifact(tmp_path)
    root = Path(result["artifact_path"])
    assert (root / "counter_machine_mapping_proof.md").exists()
    assert (root / "while_language_mapping_proof.md").exists()
    assert result["constructive_mapping_documented"] is True
    assert result["formal_turing_completeness_proven"] is False
