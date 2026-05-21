from pathlib import Path

from jianmu.self_learning.darwinforge.paper_figure_data_pack import generate_paper_figure_data_pack
from jianmu.self_learning.darwinforge.paper_figure_generator import generate_paper_figures


def test_paper_figure_generator_outputs_manifest(tmp_path):
    data = generate_paper_figure_data_pack(tmp_path / "records", tmp_path / "data")
    manifest = generate_paper_figures(tmp_path / "data", tmp_path / "figures", tmp_path / "assets")
    assert manifest["paper_figures_generated"] is True
    assert (tmp_path / "figures" / "figure_manifest.json").exists()


def test_paper_figure_generator_no_fake_data(tmp_path):
    generate_paper_figure_data_pack(tmp_path / "records", tmp_path / "data")
    generate_paper_figures(tmp_path / "data", tmp_path / "figures", tmp_path / "assets")
    assert (tmp_path / "data" / "scale_signal.csv").read_text(encoding="utf-8").count("missing") >= 1
