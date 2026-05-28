from jianmu.self_learning.darwinforge.layerwise_profile_persistence import write_layerwise_profile_state_and_reload


def test_layerwise_profile_persistence_cross_process(tmp_path):
    trace = write_layerwise_profile_state_and_reload(tmp_path, {"profiles": [{"profile_name": "layerwise_sparse_1B_freeze_prune", "frozen_state_units": 1, "pruned_state_units": 2, "transfer_hit_rate": 0.7, "active_state_units": 3, "touch_ratio": 0.1}]})
    assert trace["cross_process_reload_passed"] is True
    assert trace["child_forbidden_field_access_count"] == 0
