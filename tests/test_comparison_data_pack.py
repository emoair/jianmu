from pathlib import Path

from jianmu.self_learning.darwinforge.comparison_data_pack import generate_comparison_data_pack


def test_comparison_data_pack_outputs_csv_json(tmp_path):
    result = generate_comparison_data_pack({"mode_results": [{"mode": "large"}]}, tmp_path)
    assert result["comparison_data_pack_generated"] is True
    assert (tmp_path / "scale_vs_metric.csv").exists()
    assert (tmp_path / "scale_vs_metric.json").exists()
    assert (tmp_path / "paper_update_notes.md").exists()
