from jianmu.self_learning.darwinforge.paper_figure_data_pack import generate_paper_figure_data_pack


def test_paper_figure_data_pack_reads_records_only(tmp_path):
    records = tmp_path / "records"
    out = tmp_path / "figure_data"
    records.mkdir()
    manifest = generate_paper_figure_data_pack(records, out)
    assert manifest["paper_figure_data_pack_generated"] is True
    assert (out / "non_claims_table.csv").exists()


def test_paper_figure_data_pack_marks_missing(tmp_path):
    generate_paper_figure_data_pack(tmp_path / "empty_records", tmp_path / "out")
    assert "missing" in (tmp_path / "out" / "scale_signal.csv").read_text(encoding="utf-8")
