import json

from jianmu.self_learning.darwinforge.active_work_threshold_calibrator import calibrate_active_work_threshold


def test_active_work_threshold_calibrator_rejects_fixed_20k_45min(tmp_path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "active_backend_validation_summary.json").write_text(json.dumps({"actual_elapsed_seconds": 2821.438, "backend_cl_invocations": 12795}), encoding="utf-8")
    result = calibrate_active_work_threshold(src, tmp_path / "out")
    assert result["fixed_20k_45min_threshold_rejected"] is True
    assert result["threshold_calibration_passed"] is True


def test_active_work_threshold_calibrator_uses_observed_rate(tmp_path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "active_backend_validation_summary.json").write_text(json.dumps({"actual_elapsed_seconds": 100, "backend_cl_invocations": 500}), encoding="utf-8")
    result = calibrate_active_work_threshold(src, tmp_path / "out")
    assert result["observed_backend_rate_per_second"] == 5.0
    assert result["expected_6h_backend_invocations"] == 108000
