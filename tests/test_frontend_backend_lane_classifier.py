from jianmu.self_learning.darwinforge.frontend_backend_lane_classifier import classify_frontend_backend_lanes


def test_frontend_backend_lane_classifier_separates_events(tmp_path) -> None:
    result = classify_frontend_backend_lanes(tmp_path, frontend_events=100, backend_cl=10, backend_link=10, backend_exe=10)
    assert result["frontend_counted_as_backend"] is False
    assert result["compiler_verified_correctness_denominator"] == 10

