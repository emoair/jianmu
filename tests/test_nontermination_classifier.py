from jianmu.self_learning.darwinforge.nontermination_classifier import classify_nontermination


def test_nontermination_classifier_no_fake_expected_output():
    assert classify_nontermination("timeout_unknown", expected_output=None)["valid"] is True
    bad = classify_nontermination("timeout_unknown", expected_output="42")
    assert bad["valid"] is False
    assert bad["fake_expected_output_detected"] is True
