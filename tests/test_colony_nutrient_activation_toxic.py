from jianmu.self_learning.darwinforge.toxic_nutrient import compute_nutrient_signal


def test_ood_false_accept_counts_as_toxic_nutrient():
    signal = compute_nutrient_signal({"unsupported_pred": False, "target_ir_pred": "lit(1)"}, {"supported": False, "input_mode": "ood_english"})
    assert signal.toxic_nutrient > 0
    assert signal.toxicity_reason == "ood_false_accept"


def test_correct_ood_rejection_counts_as_positive_nutrient():
    signal = compute_nutrient_signal({"unsupported_pred": True}, {"supported": False, "input_mode": "ood_unrelated"})
    assert signal.positive_nutrient > 0
    assert signal.positive_reason == "correct_ood_rejection"


def test_unsupported_arithmetic_false_accept_counts_as_toxic():
    signal = compute_nutrient_signal({"unsupported_pred": False, "target_ir_pred": "div(lit(1),lit(0))"}, {"supported": False, "input_mode": "unsupported_arithmetic", "unsupported_reason": "division_by_zero"})
    assert signal.toxic_nutrient > 0
    assert signal.toxicity_reason == "unsupported_arithmetic_false_accept"


def test_high_confidence_wrong_counts_as_toxic():
    signal = compute_nutrient_signal({"rank": 1, "target_ir_pred": "lit(2)", "target_ir_exact_match": False}, {"supported": True})
    assert signal.toxicity_reason == "high_confidence_wrong_targetir"
