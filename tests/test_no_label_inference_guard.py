from jianmu.self_learning.darwinforge.no_label_inference_guard import assert_no_label_fields_used


def test_no_label_inference_guard_blocks_boundary_label_access():
    result = assert_no_label_fields_used([{"sample_id": "s1", "field": "boundary_label"}])
    assert result["no_label_inference_passed"] is False
    assert result["forbidden_field_access_count"] == 1


def test_no_label_inference_guard_blocks_expected_action_access():
    result = assert_no_label_fields_used([{"sample_id": "s1", "field": "expected_action"}])
    assert "expected_action" in result["forbidden_fields_seen"]


def test_no_label_inference_guard_blocks_targetir_access():
    result = assert_no_label_fields_used([{"sample_id": "s1", "field": "target_ir"}])
    assert result["violation_examples"][0]["field"] == "target_ir"
