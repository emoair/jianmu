from jianmu.self_learning.darwinforge.boundary_reward_adapter import compute_boundary_reward


def test_boundary_reward_current_supported_correct_accept_positive():
    sig = compute_boundary_reward({"boundary_label": "current_supported", "training_usage": "train_current"}, {"accepted_as_supported": True, "targetir_exact_match": True})
    assert sig.positive_reward > 0
    assert sig.toxicity == 0


def test_boundary_reward_hard_ood_false_accept_toxic():
    sig = compute_boundary_reward({"boundary_label": "hard_ood", "training_usage": "train_reject_boundary"}, {"accepted_as_supported": True})
    assert sig.toxicity >= 2.0


def test_boundary_reward_trap_false_accept_strong_toxic():
    sig = compute_boundary_reward({"boundary_label": "true_false_accept_trap", "training_usage": "train_reject_boundary"}, {"accepted_as_supported": True})
    assert sig.toxicity > 2.0


def test_boundary_reward_future_domain_not_positive_supported():
    sig = compute_boundary_reward({"boundary_label": "future_domain_candidate", "training_usage": "future_buffer_only"}, {"accepted_as_supported": True})
    assert sig.positive_reward == 0
    assert sig.toxicity > 0
