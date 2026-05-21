from jianmu.self_learning.datasets.boundary_aware_generator import generate_boundary_aware_samples
from jianmu.self_learning.datasets.boundary_labels import boundary_label_values


def test_boundary_generator_generates_all_labels():
    rows = generate_boundary_aware_samples(600, seed=42)
    labels = {row["boundary_label"] for row in rows}
    assert set(boundary_label_values()).issubset(labels)
