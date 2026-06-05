from jianmu.self_learning.darwinforge.csystems_frontier_schema import CSystemsFrontierConfig, CSystemsScaleConfig


def test_csystems_frontier_config_contains_pointer_malloc_fileio_multifile_struct():
    families = CSystemsFrontierConfig.families()
    assert "pointer_frontier" in families
    assert "malloc_frontier" in families
    assert "fileio_frontier" in families
    assert "multifile_frontier" in families
    assert "struct_frontier" in families


def test_csystems_dataset_requires_full_scale():
    cfg = CSystemsScaleConfig.for_scale("full")
    assert cfg.total == 5_000_000
    assert cfg.full_compile_target == 50_000
