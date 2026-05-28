from jianmu.self_learning.darwinforge.turing_frontier_v2_generator import generate_turing_frontier_v2_dataset, make_frontier_v2_sample


def test_turing_frontier_v2_generation(tmp_path):
    result = generate_turing_frontier_v2_dataset(tmp_path / "ds", tmp_path / "records", ["pilot"], shard_size=100000)
    assert result["scales"]["pilot"]["actual_total"] == 50000


def test_turing_frontier_v2_audit_blocks_review_train():
    row = make_frontier_v2_sample(1, "pilot", "label_review_candidate")
    assert row["split"] != "train"
