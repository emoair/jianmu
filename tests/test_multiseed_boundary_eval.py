from jianmu.self_learning.darwinforge.multiseed_boundary_eval import run_multiseed_boundary_eval


def test_multiseed_boundary_eval_reports_all_seeds():
    samples = [
        {"sample_id": "s1", "raw_text": "3+4", "input_mode": "current_supported", "boundary_label": "current_supported"},
        {"sample_id": "s2", "raw_text": "写诗", "input_mode": "hard_ood", "boundary_label": "hard_ood"},
    ]
    result = run_multiseed_boundary_eval(samples, {"persisted_state_support_level": "summary_only"}, [42, 43, 44])
    assert result["seeds"] == [42, 43, 44]


def test_multiseed_stability_requires_all_seeds_safe():
    samples = [
        {"sample_id": "s1", "raw_text": "3+4", "input_mode": "current_supported", "boundary_label": "current_supported"},
        {"sample_id": "s2", "raw_text": "写诗", "input_mode": "hard_ood", "boundary_label": "hard_ood"},
    ]
    result = run_multiseed_boundary_eval(samples, {"persisted_state_support_level": "summary_only"}, [42, 43, 44])
    assert result["stable_across_seeds"] is True
