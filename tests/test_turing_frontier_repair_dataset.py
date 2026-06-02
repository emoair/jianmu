from jianmu.self_learning.darwinforge.turing_frontier_repair_dataset import audit_repair_dataset, generate_repair_dataset


def test_repair_dataset_contract_clean(tmp_path):
    dataset = tmp_path / "dataset"
    records = tmp_path / "records"
    manifest = generate_repair_dataset(dataset, target_samples=1000)
    audit = audit_repair_dataset(dataset, records)
    assert manifest["total_samples"] == 1000
    assert manifest["max_shard_size"] < 45 * 1024 * 1024
    assert audit["audit_passed"] is True
    assert audit["unbounded_in_current_supported_count"] == 0
    assert audit["recursion_in_current_supported_count"] == 0
    assert audit["state_growth_in_current_supported_count"] == 0
