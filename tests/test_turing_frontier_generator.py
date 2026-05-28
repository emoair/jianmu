from __future__ import annotations

import json

from jianmu.self_learning.darwinforge.turing_frontier_generator import generate_turing_frontier_dataset


def test_turing_frontier_dataset_generation(monkeypatch, tmp_path) -> None:
    import jianmu.self_learning.darwinforge.turing_frontier_generator as gen

    monkeypatch.setitem(gen.SCALE_TOTALS, "small", 100)
    result = generate_turing_frontier_dataset(tmp_path / "dataset", tmp_path / "records", ["small"], 68, 50)
    assert result["scales_completed"] == ["small"]
    manifest = json.loads((tmp_path / "dataset" / "small" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["actual_total"] == 100

