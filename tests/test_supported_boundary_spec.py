from jianmu.self_learning.darwinforge.supported_boundary_spec import classify_against_supported_boundary, default_supported_boundary_spec


def test_supported_boundary_spec_classifies_current_supported():
    spec = default_supported_boundary_spec()
    decision = classify_against_supported_boundary({}, "计算三加四", "3+4", {},)
    assert decision.boundary_label == "supported"
    assert decision.recommended_action == "keep_supported"
    assert spec.version == "v0.8.4"


def test_supported_boundary_spec_classifies_future_domain():
    decision = classify_against_supported_boundary({"ood_class": "non_exact_division"}, "输出 5/4", "5/4", {"ood_class": "non_exact_division"})
    assert decision.boundary_label == "future_domain_candidate"
    assert decision.recommended_action == "future_domain"


def test_supported_boundary_spec_classifies_hard_reject():
    decision = classify_against_supported_boundary({"ood_class": "ood_unrelated_request"}, "写一首诗", "写1首诗", {"ood_class": "ood_unrelated_request"})
    assert decision.boundary_label == "hard_reject"
    assert decision.recommended_action == "reject_guard_needed"
