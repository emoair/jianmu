from jianmu.self_learning.darwinforge.real_ir_emitter_validation import run_real_ir_emitter_validation


def test_real_ir_emitter_validation(tmp_path):
    result = run_real_ir_emitter_validation(tmp_path, target_total=6)
    assert result["validation_completed"] is True
    assert result["cached_result_used_as_new_count"] == 0
    assert result["stubbed_validation_detected"] is False
    assert result["summary_only_validation_detected"] is False

