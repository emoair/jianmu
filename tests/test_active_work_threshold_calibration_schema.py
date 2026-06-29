from jianmu.self_learning.darwinforge.active_work_threshold_calibration_schema import ActiveWorkThresholdCalibrationConfig, calibration_contract


def test_active_work_threshold_calibration_schema() -> None:
    cfg = ActiveWorkThresholdCalibrationConfig()
    assert cfg.fixed_threshold_invocations == 20000
    assert calibration_contract()["fixed_20k_45min_threshold_rejected"] is True
