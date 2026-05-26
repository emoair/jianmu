from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.turing_substrate_boundary_labels import SUPPORTED
from jianmu.self_learning.darwinforge.turing_substrate_generator import generate_scale


def test_turing_substrate_non_supported_has_no_targetir(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setitem(__import__("jianmu.self_learning.darwinforge.turing_substrate_generator", fromlist=["SCALE_TOTALS"]).SCALE_TOTALS, "small", 200)
    result = generate_scale("small", tmp_path / "small", seed=52, shard_size=100)
    rows = list((tmp_path / "small").glob("*/*.jsonl"))
    assert result["audit"]["non_supported_has_targetir_count"] == 0
    assert rows


def test_turing_substrate_supported_has_expected_output(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setitem(__import__("jianmu.self_learning.darwinforge.turing_substrate_generator", fromlist=["SCALE_TOTALS"]).SCALE_TOTALS, "small", 200)
    result = generate_scale("small", tmp_path / "small", seed=53, shard_size=100)
    assert result["audit"]["supported_missing_expected_output_count"] == 0
    assert result["audit"]["category_count"][SUPPORTED] > 0
