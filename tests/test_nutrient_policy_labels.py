from jianmu.self_learning.datasets.boundary_labels import BoundaryLabel
from jianmu.self_learning.datasets.nutrient_policy_labels import nutrient_policy_for_boundary


def test_true_false_accept_has_toxic_pressure():
    policy = nutrient_policy_for_boundary(BoundaryLabel.TRUE_FALSE_ACCEPT_TRAP.value)
    assert policy["false_accept_toxicity"] > 0
    assert policy["accept_reward"] == 0


def test_hard_ood_has_toxic_pressure():
    policy = nutrient_policy_for_boundary(BoundaryLabel.HARD_OOD.value)
    assert policy["false_accept_toxicity"] > 0
    assert policy["reject_reward"] > 0
