from jianmu.self_learning.darwinforge.symbiote_snapshot import create_symbiote_snapshots


def test_symbiote_snapshot_created_and_restored(tmp_path):
    result = create_symbiote_snapshots(tmp_path)
    assert result["snapshots_created"] is True
    assert result["snapshot_restore_passed"] is True
    assert result["neural_framework_used"] is False
