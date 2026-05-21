from jianmu.self_learning.darwinforge.ood_boundary_classifier import classify_ood_boundary_samples


def test_ood_boundary_classifier_separates_true_false_accept():
    result = classify_ood_boundary_samples(
        [{"sample_id": "s1", "raw_text": "写一首诗", "canonical_text": "写1首诗", "ood_class": "ood_unrelated_request", "accepted_as_supported": True}]
    )
    assert result["true_false_accept_count"] == 1


def test_ood_boundary_classifier_separates_near_generalization():
    result = classify_ood_boundary_samples(
        [{"sample_id": "s1", "raw_text": "帮我算一下三加四", "canonical_text": "3+4", "ood_class": "unknown", "accepted_as_supported": True}]
    )
    assert result["near_ood_generalization_candidate_count"] == 1


def test_ood_boundary_classifier_separates_future_domain():
    result = classify_ood_boundary_samples(
        [{"sample_id": "s1", "raw_text": "输出 5/4", "canonical_text": "5/4", "ood_class": "non_exact_division", "accepted_as_supported": True}]
    )
    assert result["future_domain_candidate_count"] == 1
