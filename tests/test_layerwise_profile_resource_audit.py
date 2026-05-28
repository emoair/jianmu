from jianmu.self_learning.darwinforge.layerwise_profile_resource_audit import build_layerwise_profile_resource_audit


def test_layerwise_profile_resource_audit(tmp_path):
    shadow = {"profiles": [
        {"profile_name": "combined_hot_rebalanced_balanced_sampling_1B", "runtime_seconds": 10, "samples_per_second": 100, "peak_memory_bytes": 100, "disk_bytes_written": 3, "active_state_units": 10, "touch_ratio": 0.1, "hot_state_ratio": 0.01, "cold_state_ratio": 0.99, "top1_correct_rate": 0.8},
        {"profile_name": "layerwise_sparse_1B_freeze_prune", "runtime_seconds": 12, "samples_per_second": 90, "peak_memory_bytes": 200, "disk_bytes_written": 6, "active_state_units": 20, "touch_ratio": 0.15, "hot_state_ratio": 0.02, "cold_state_ratio": 0.98, "frozen_state_units": 1, "pruned_state_units": 2, "top1_correct_rate": 0.83},
    ]}
    audit = build_layerwise_profile_resource_audit(tmp_path, shadow, {"per_profile": {}}, {"cross_process_reload_seconds": 0.1})
    assert audit["layerwise_resource_overhead_acceptable"] is True
