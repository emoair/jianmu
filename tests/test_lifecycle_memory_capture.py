from jianmu.self_learning.darwinforge.lifecycle_memory_capture import capture_lifecycle_runtime_state


def test_runtime_state_capture_records_lifecycle_states():
    training = {
        "stage_metrics": [
            {
                "stage_name": "stage_1",
                "sample_count": 3,
                "before_metrics": {"overall_ood_false_accept_rate": 1.0, "current_supported_retention_rate": 1.0},
                "after_metrics": {"overall_ood_false_accept_rate": 0.0, "current_supported_retention_rate": 1.0},
                "accepted_as_supported_count": 1,
                "rejected_count": 2,
                "false_accept_count": 0,
                "false_reject_count": 0,
            }
        ],
        "rejection_layer_distribution": {"after": {"support_gate": 2}},
    }
    roots = {"stable_roots": [{"id": "r"}], "nourished_roots": [], "starving_roots": [], "necrotic_roots": [], "replacement_roots": []}
    state = capture_lifecycle_runtime_state(training, roots)
    assert state.nourishment_events == 1
    assert state.accepted_rejected_distribution["rejected"] == 2
