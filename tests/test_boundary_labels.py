from jianmu.self_learning.datasets.boundary_aware_generator import generate_boundary_aware_samples
from jianmu.self_learning.datasets.boundary_labels import BoundaryLabel, validate_boundary_sample


def test_boundary_labels_required_fields():
    sample = generate_boundary_aware_samples(20, seed=1)[0]
    assert validate_boundary_sample(sample) == []


def test_current_supported_requires_targetir():
    sample = next(row for row in generate_boundary_aware_samples(100, seed=2) if row["boundary_label"] == BoundaryLabel.CURRENT_SUPPORTED.value)
    assert sample["target_ir"]
    assert sample["expected_output"]


def test_non_supported_must_not_have_targetir():
    rows = [row for row in generate_boundary_aware_samples(100, seed=3) if row["boundary_label"] != BoundaryLabel.CURRENT_SUPPORTED.value]
    assert rows
    assert all("target_ir" not in row and "expected_output" not in row for row in rows)


def test_future_domain_not_train_current():
    row = next(row for row in generate_boundary_aware_samples(100, seed=4) if row["boundary_label"] == BoundaryLabel.FUTURE_DOMAIN_CANDIDATE.value)
    assert row["training_usage"] == "future_buffer_only"


def test_near_ood_not_train_current():
    row = next(row for row in generate_boundary_aware_samples(100, seed=5) if row["boundary_label"] == BoundaryLabel.NEAR_OOD_GENERALIZATION_CANDIDATE.value)
    assert row["training_usage"] == "audit_only"
