from __future__ import annotations

from jianmu.self_learning.darwinforge.contrastive_forge_generator import generate_contrastive_forge_dataset


def test_contrastive_forge_pair_integrity(tmp_path) -> None:
    result = generate_contrastive_forge_dataset(tmp_path, {"pilot": 90})
    assert result["scales"]["pilot"]["declared_total"] == 90
    assert (tmp_path / "pilot" / "train_00000.jsonl").exists()
