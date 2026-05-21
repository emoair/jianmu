from jianmu.self_learning.darwinforge.full_state_reloader import load_full_state
from jianmu.self_learning.darwinforge.full_state_serializer import save_full_state


def test_full_state_reloader_checksum_match(tmp_path):
    records = tmp_path / "records"
    records.mkdir()
    save_full_state(records, tmp_path / "state")
    loaded = load_full_state(tmp_path / "state")
    assert loaded["checksum_match"] is True


def test_full_state_reloader_fails_missing_required_state(tmp_path):
    records = tmp_path / "records"
    records.mkdir()
    save_full_state(records, tmp_path / "state")
    (tmp_path / "state" / "full_router_state.json").unlink()
    loaded = load_full_state(tmp_path / "state")
    assert loaded["state_loaded"] is False
    assert "full_router_state.json" in loaded["missing_state_files"]
