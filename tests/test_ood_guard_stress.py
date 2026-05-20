from jianmu.self_learning.darwinforge.ood_guard_stress import run_ood_guard_stress


def test_ood_guard_stress_records_false_accept_reason():
    result = run_ood_guard_stress(None, [{"sample_id": "a", "input_mode": "ood_english", "input_text": "hello"}], {"baseline_ood_false_accept_rate": 1.0})
    assert result["records"][0]["false_accept_reason"] != "none"


def test_ood_guard_stress_groups_by_class():
    result = run_ood_guard_stress(None, [{"sample_id": "a", "input_mode": "ood_english", "input_text": "hello"}], {"baseline_ood_false_accept_rate": 1.0})
    assert result["ood_false_accept_by_class"]["ood_english_sentence"] == 1
