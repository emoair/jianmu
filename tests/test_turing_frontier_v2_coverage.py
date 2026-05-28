from jianmu.self_learning.darwinforge.turing_frontier_v2_audit import audit_turing_frontier_v2_dataset
from jianmu.self_learning.darwinforge.turing_frontier_v2_coverage import summarize_turing_frontier_v2_coverage
from jianmu.self_learning.darwinforge.turing_frontier_v2_generator import generate_turing_frontier_v2_dataset


def test_turing_frontier_v2_coverage_map(tmp_path):
    ds = tmp_path / "ds"
    generate_turing_frontier_v2_dataset(ds, tmp_path / "records", ["pilot"], shard_size=100000)
    audit_turing_frontier_v2_dataset(ds)
    coverage = summarize_turing_frontier_v2_coverage(ds, tmp_path / "records")
    assert coverage["dataset_v2_ready_for_active_generation_loop"] is True
