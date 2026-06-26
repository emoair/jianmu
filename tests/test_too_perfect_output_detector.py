from jianmu.self_learning.darwinforge.too_perfect_output_detector import detect_too_perfect_output


def test_too_perfect_output_detector_flags_planned_as_actual() -> None:
    result = detect_too_perfect_output({"planned_wall_clock_hours": 8.0, "actual_wall_clock_hours": 8.0}, [])
    assert result["planned_as_actual_detected"] is True
    assert result["too_perfect_output_detected"] is True
