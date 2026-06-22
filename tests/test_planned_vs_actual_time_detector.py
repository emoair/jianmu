from jianmu.self_learning.darwinforge.planned_vs_actual_time_detector import audit_planned_vs_actual_time_code


def test_planned_vs_actual_detector_flags_args_min_hours_assignment(tmp_path):
    examples = tmp_path / "examples"
    package = tmp_path / "jianmu" / "self_learning" / "darwinforge"
    examples.mkdir()
    package.mkdir(parents=True)
    (examples / "bad.py").write_text('summary = {"wall_clock_hours": args.wall_clock_min_hours}\n', encoding="utf-8")
    result = audit_planned_vs_actual_time_code(tmp_path)
    assert result["dangerous_time_patterns_found"]
    assert result["code_audit_passed_after_fix"] is False
