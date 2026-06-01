from jianmu.self_learning.darwinforge.turing_frontier_dataset_builder import generate_turing_frontier_dataset


def test_turing_frontier_dataset_builder(tmp_path):
    manifest = generate_turing_frontier_dataset(tmp_path, target_samples=1000)
    assert manifest["total_samples"] == 1000
    assert manifest["max_shard_size"] < 45 * 1024 * 1024
