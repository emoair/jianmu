from jianmu.self_learning.darwinforge.turing_frontier_v2_audit import audit_turing_frontier_v2_dataset
from jianmu.self_learning.darwinforge.turing_frontier_v2_generator import generate_turing_frontier_v2_dataset


def test_turing_frontier_v2_audit_blocks_future_targets(tmp_path):
    ds = tmp_path / "ds"
    generate_turing_frontier_v2_dataset(ds, tmp_path / "records", ["pilot"], shard_size=100000)
    audit = audit_turing_frontier_v2_dataset(ds)
    assert audit["scales"]["pilot"]["non_supported_has_targetir_count"] == 0
    assert audit["scales"]["pilot"]["audit_passed"] is True
