from jianmu.self_learning.darwinforge.ood_toxicity_taxonomy import classify_ood_sample


def test_ood_taxonomy_classifies_english_sentence():
    klass = classify_ood_sample({"input_mode": "ood_english", "input_text": "please calculate this"})
    assert klass.class_id == "ood_english_sentence"


def test_ood_taxonomy_classifies_unrelated_request():
    klass = classify_ood_sample({"input_mode": "ood_unrelated", "input_text": "查天气"})
    assert klass.class_id == "ood_unrelated_request"


def test_ood_taxonomy_classifies_division_by_zero():
    klass = classify_ood_sample({"input_mode": "unsupported_arithmetic", "unsupported_reason": "division_by_zero", "input_text": "1/0"})
    assert klass.class_id == "division_by_zero"


def test_ood_taxonomy_classifies_non_exact_division():
    klass = classify_ood_sample({"input_mode": "unsupported_arithmetic", "unsupported_reason": "non_exact_division"})
    assert klass.class_id == "non_exact_division"
