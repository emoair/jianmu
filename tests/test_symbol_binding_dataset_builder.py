from jianmu.self_learning.darwinforge.symbol_binding_dataset_builder import build_symbol_binding_dataset, iter_symbol_rows


def test_symbol_binding_dataset_builder(tmp_path):
    manifest = build_symbol_binding_dataset(tmp_path / "ds", "pilot", seed=185)
    assert manifest["total_samples"] == 100_000
    first = next(iter_symbol_rows(tmp_path / "ds"))
    assert first["provenance"]["llm_generated"] is False

