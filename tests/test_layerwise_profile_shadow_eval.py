from jianmu.self_learning.darwinforge.layerwise_profile_shadow_eval import run_layerwise_profile_shadow_eval


def test_layerwise_profile_not_default_runtime(tmp_path):
    dataset = tmp_path / "large" / "train"
    dataset.mkdir(parents=True)
    row = '{"id":"a","category":"current_supported_bounded_substrate","split":"train"}\n'
    (dataset / "data.jsonl").write_text(row, encoding="utf-8")
    result = run_layerwise_profile_shadow_eval(tmp_path, tmp_path / "out", ["current_1B_reference"], samples=1, boundary_samples=0)
    assert result["profiles"][0]["profile_is_default_runtime"] is False
    assert result["profiles"][0]["profile_is_architecture_change"] is False
