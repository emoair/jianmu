from jianmu.self_learning.darwinforge.turing_frontier_audit import audit_dataset
from jianmu.self_learning.darwinforge.turing_frontier_dataset_builder import generate_turing_frontier_dataset


def test_turing_frontier_dataset_audit_no_current_supported_pollution(tmp_path):
    dataset = tmp_path / "dataset"
    records = tmp_path / "records"
    generate_turing_frontier_dataset(dataset, target_samples=1000)
    audit = audit_dataset(dataset, records)
    assert audit["audit_passed"] is True
    assert audit["unbounded_in_current_supported_count"] == 0
    assert audit["recursion_in_current_supported_count"] == 0
    assert audit["expected_output_on_unknown_halting_count"] == 0
