from jianmu.self_learning.darwinforge.mirror_redqueen_distribution_audit import audit_distribution


def test_mirror_redqueen_distribution_audit_requires_plan_follow(tmp_path) -> None:
    cycles = [{"execution": {"plan_follow_rate": 0.96, "planned_category_distribution": {"mixed": 1}, "actual_category_distribution": {"mixed": 1}}}]
    result = audit_distribution(tmp_path, cycles)
    assert result["distribution_audit_passed"] is True

