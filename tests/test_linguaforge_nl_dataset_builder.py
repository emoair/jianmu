from jianmu.self_learning.darwinforge.linguaforge_nl_dataset_builder import build_linguaforge_dataset, iter_linguaforge_rows


def test_linguaforge_nl_dataset_builder(tmp_path):
    manifest = build_linguaforge_dataset(tmp_path / "ds", "pilot", 1000, 188)
    assert manifest["dataset_generated"]
    assert manifest["total_samples"] == 1000
    assert len(list(iter_linguaforge_rows(tmp_path / "ds"))) == 1000
