from jianmu.self_learning.darwinforge.controlled_profile_review_schema import ControlledProfileReviewConfig, check_v1_0_6_records


def test_controlled_profile_review_schema():
    config = ControlledProfileReviewConfig()
    assert config.replay_samples == 2000
    assert config.rollback_cycles == 100


def test_missing_v1_0_6_records_detected(tmp_path):
    result = check_v1_0_6_records(tmp_path)
    assert result["source_dry_run_records_found"] is False
    assert "shadow_profile_config.json" in result["missing_required_files"]
