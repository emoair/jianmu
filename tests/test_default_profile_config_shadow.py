from jianmu.self_learning.darwinforge.default_profile_config_shadow import build_default_profile_dryrun_config


def test_default_profile_shadow_config_loads_layerwise(tmp_path):
    cfg = build_default_profile_dryrun_config(tmp_path)
    assert cfg["dry_run_default_profile_name"] == "layerwise_sparse_1B_freeze_prune"
    assert cfg["real_promotion_enabled"] is False
    assert cfg["production_config_modified"] is False
