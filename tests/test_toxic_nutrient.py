from jianmu.self_learning.darwinforge.toxic_nutrient import compute_nutrient_signal


def test_toxic_nutrient_ood_false_accept_penalty():
    signal = compute_nutrient_signal({"unsupported_pred": False}, {"supported": False})

    assert signal.toxic_nutrient > 0
    assert signal.toxicity_reason == "ood_false_accept"


def test_correct_ood_rejection_positive_nutrient():
    signal = compute_nutrient_signal({"unsupported_pred": True}, {"supported": False})

    assert signal.positive_nutrient > 0
    assert signal.toxic_nutrient == 0
