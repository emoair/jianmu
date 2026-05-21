from jianmu.self_learning.darwinforge.ood_precision_recheck import OODPrecisionAuditConfig, run_ood_precision_recheck


def test_ood_precision_recheck_outputs_examples():
    samples = [{"sample_id": "1", "input_text": "write a poem", "input_mode": "ood_english"}]
    guards = [{"sample_id": "1", "ood_class": "ood_english_sentence", "accepted_as_supported": True}]
    result = run_ood_precision_recheck(samples, guards, OODPrecisionAuditConfig(max_examples_per_class=2))
    assert result["examples_by_precision_label"]["true_false_accept"]


def test_ood_precision_recheck_separates_true_false_accept_and_near_generalization():
    samples = [
        {"sample_id": "1", "input_text": "write a poem", "input_mode": "ood_english"},
        {"sample_id": "2", "input_text": "帮我算一下三加四", "input_mode": "ood_unrelated"},
    ]
    guards = [
        {"sample_id": "1", "ood_class": "ood_english_sentence", "accepted_as_supported": True},
        {"sample_id": "2", "ood_class": "mixed_language_query", "accepted_as_supported": True, "false_accept_reason": "canonicalizer_made_it_look_supported"},
    ]
    result = run_ood_precision_recheck(samples, guards)
    assert result["true_false_accept_count"] == 1
    assert result["near_ood_generalization_candidate_count"] == 1

