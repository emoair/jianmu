from jianmu.self_learning.darwinforge.nutrient_toxic_memory_capture import capture_nutrient_toxic_runtime_memory


def test_runtime_state_capture_records_nutrient_toxic_memory():
    state = capture_nutrient_toxic_runtime_memory(
        {
            "reward_records": [
                {"boundary_label": "hard_ood", "positive_reward": 1.0, "toxicity": 0.0, "training_usage": "train_reject_boundary"},
                {"boundary_label": "future_domain_candidate", "positive_reward": 0.0, "toxicity": 0.5, "training_usage": "future_buffer_only", "toxicity_reason": "false accept"},
            ]
        }
    )
    assert state.positive_nutrient_events == 1
    assert state.toxic_events == 1
    assert state.future_domain_buffer_events == 1
