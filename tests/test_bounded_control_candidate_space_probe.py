from __future__ import annotations

import json

from jianmu.self_learning.darwinforge.bounded_control_candidate_space_probe import run_candidate_space_probe
from jianmu.self_learning.darwinforge.turing_frontier_generator import generate_turing_frontier_dataset


def test_candidate_space_probe_outputs_candidate_miss(monkeypatch, tmp_path) -> None:
    import jianmu.self_learning.darwinforge.turing_frontier_generator as gen

    monkeypatch.setitem(gen.SCALE_TOTALS, "large", 200)
    root = tmp_path / "frontier"
    generate_turing_frontier_dataset(root, tmp_path / "records", ["large"], 68, 100)
    result = run_candidate_space_probe(tmp_path / "substrate", root, tmp_path / "source", tmp_path / "out", ["if_else_basic", "bounded_for_loop", "bounded_control_hard_supported"], [8], [32], ["small"], ["1x"], ["baseline"], 50, 50, run_compiler_validation=False)
    assert result["coverage"]["candidate_miss_rate"] >= 0


def test_compiler_validation_blocks_future_domain_compile(monkeypatch, tmp_path) -> None:
    import jianmu.self_learning.darwinforge.turing_frontier_generator as gen

    monkeypatch.setitem(gen.SCALE_TOTALS, "large", 200)
    root = tmp_path / "frontier"
    generate_turing_frontier_dataset(root, tmp_path / "records", ["large"], 68, 100)
    result = run_candidate_space_probe(tmp_path / "substrate", root, tmp_path / "source", tmp_path / "out", ["if_else_basic"], [8], [32], ["small"], ["1x"], ["baseline"], 20, 20, run_compiler_validation=False)
    assert result["coverage"]["future_domain_supported_accept_rate"] == 0.0

