from jianmu.self_learning.darwinforge.external_ood_slice import generate_external_ood_slice


def test_external_ood_slice_generates_categories(tmp_path):
    result = generate_external_ood_slice("quick", tmp_path)
    dist = result["manifest"]["category_distribution"]
    assert set(dist) == {"external_hard_ood", "external_arithmetic_traps", "external_future_domain", "external_near_ood"}
    assert result["manifest"]["external_ood_total_count"] == 800


def test_external_ood_slice_not_training_data(tmp_path):
    result = generate_external_ood_slice("quick", tmp_path)
    assert result["manifest"]["contains_training_rows"] is False
    assert all("target_ir" not in row and "expected_output" not in row for row in result["samples"])
