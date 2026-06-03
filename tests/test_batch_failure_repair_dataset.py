from jianmu.self_learning.darwinforge.batch_failure_repair_dataset import generate_repair_dataset


def test_repair_dataset_contract_clean(tmp_path):
    result = generate_repair_dataset(tmp_path / "dataset", tmp_path / "records", target_samples=1000)
    assert result["repair_dataset_generated"] is True
    assert result["total_samples"] == 1000
    assert result["audit_passed"] is True
    assert result["max_shard_size"] <= 45_000_000
