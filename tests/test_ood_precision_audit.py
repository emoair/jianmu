from jianmu.self_learning.darwinforge.ood_precision_audit import label_ood_precision, run_ood_precision_audit


def test_ood_precision_audit_labels_hard_ood():
    sample = {"sample_id": "1", "input_text": "write a poem", "input_mode": "ood_english"}
    record = {"sample_id": "1", "ood_class": "ood_english_sentence", "accepted_as_supported": True, "generated_targetir": True}
    assert label_ood_precision(sample, record).precision_label == "true_false_accept"


def test_ood_precision_audit_labels_near_generalization_candidate():
    sample = {"sample_id": "1", "input_text": "帮我算一下三加四", "input_mode": "ood_unrelated"}
    record = {"sample_id": "1", "ood_class": "mixed_language_query", "accepted_as_supported": True, "false_accept_reason": "canonicalizer_made_it_look_supported"}
    assert label_ood_precision(sample, record).precision_label == "near_ood_generalization_candidate"


def test_ood_precision_audit_labels_future_domain_candidate():
    sample = {"sample_id": "1", "input_text": "5/2", "input_mode": "unsupported_arithmetic"}
    record = {"sample_id": "1", "ood_class": "non_exact_division", "accepted_as_supported": True}
    assert label_ood_precision(sample, record).precision_label == "future_domain_candidate"


def test_ood_precision_summary_counts():
    samples = [{"sample_id": "1", "input_text": "write a poem", "input_mode": "ood_english"}]
    guards = [{"sample_id": "1", "ood_class": "ood_english_sentence", "accepted_as_supported": True}]
    summary = run_ood_precision_audit(samples, guards)
    assert summary["true_false_accept_count"] == 1

