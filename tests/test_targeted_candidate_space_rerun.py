from __future__ import annotations

from jianmu.self_learning.darwinforge.targeted_candidate_space_rerun import run_targeted_candidate_space_rerun
from jianmu.self_learning.darwinforge.turing_frontier_generator import generate_turing_frontier_dataset


def test_targeted_rerun_uses_fresh_samples(monkeypatch, tmp_path) -> None:
    import jianmu.self_learning.darwinforge.turing_frontier_generator as gen

    monkeypatch.setitem(gen.SCALE_TOTALS, "large", 400)
    root = tmp_path / "frontier"
    generate_turing_frontier_dataset(root, tmp_path / "records", ["large"], 68, 100)
    source = tmp_path / "source"
    source.mkdir()
    (source / "budget_sweep_metrics.json").write_text(
        '{"candidate_miss_rate_before":0.6024,"correct_output_in_beam_before":0.3776,"top1_before":0.3776}',
        encoding="utf-8",
    )
    result = run_targeted_candidate_space_rerun(
        tmp_path / "substrate",
        root,
        source,
        tmp_path / "baseline",
        tmp_path / "out",
        ["quick"],
        [70],
        samples=50,
        boundary_samples=50,
        run_compiler_validation=False,
        progress=False,
    )
    assert result["rerun"]["fresh_ratio"] >= 0.90
    assert result["rerun"]["candidate_miss_rate_targeted"] < result["rerun"]["candidate_miss_rate_baseline_reference"]


def test_cross_process_reload_for_targeted_profile(monkeypatch, tmp_path) -> None:
    import jianmu.self_learning.darwinforge.turing_frontier_generator as gen

    monkeypatch.setitem(gen.SCALE_TOTALS, "large", 400)
    root = tmp_path / "frontier"
    generate_turing_frontier_dataset(root, tmp_path / "records", ["large"], 68, 100)
    result = run_targeted_candidate_space_rerun(
        tmp_path / "substrate",
        root,
        tmp_path / "source",
        tmp_path / "baseline",
        tmp_path / "out",
        ["quick"],
        [70],
        samples=50,
        boundary_samples=50,
        run_compiler_validation=False,
        run_cross_process=True,
        progress=False,
    )
    assert result["cross_process"]["cross_process_reload_passed"] is True

