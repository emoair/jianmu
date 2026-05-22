from jianmu.self_learning.darwinforge.expanded_external_ood import REQUIRED_EXPANDED_OOD_CLASSES, evaluate_expanded_external_ood, generate_expanded_external_ood


def test_expanded_external_ood_has_required_classes():
    result = generate_expanded_external_ood("quick")
    classes = set(result["manifest"]["class_distribution"])
    assert set(REQUIRED_EXPANDED_OOD_CLASSES).issubset(classes)


def test_external_ood_does_not_read_forbidden_fields():
    result = generate_expanded_external_ood("quick")
    for row in result["samples"]:
        assert "target_ir" not in row
        assert "expected_output" not in row
        assert "target_branch_path" not in row
    metrics = evaluate_expanded_external_ood(result["samples"])
    assert metrics["external_ood_false_accept_rate"] == 0.0
