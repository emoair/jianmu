from jianmu.self_learning.darwinforge.reloaded_freebeam_eval import run_reloaded_freebeam_eval


def test_reloaded_freebeam_eval_runs_no_label():
    samples = [
        {"sample_id": "s1", "raw_text": "3+4", "input_mode": "current_supported", "boundary_label": "current_supported"},
        {"sample_id": "s2", "raw_text": "写诗", "input_mode": "hard_ood", "boundary_label": "hard_ood"},
    ]
    result = run_reloaded_freebeam_eval(samples, {"persisted_state_support_level": "summary_only"}, mode="quick")
    assert result["reloaded_eval_completed"] is True
    assert result["no_label_inference_passed"] is True
    assert result["forbidden_field_access_count"] == 0
