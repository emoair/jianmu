import json

from jianmu.self_learning.darwinforge.full_state_serializer import save_full_state, scan_state_for_forbidden_fields


def test_full_state_serializer_writes_manifest(tmp_path):
    records = tmp_path / "records"
    records.mkdir()
    result = save_full_state(records, tmp_path / "state")
    assert result["state_saved"] is True
    assert (tmp_path / "state" / "full_state_manifest.json").exists()


def test_full_state_serializer_scans_forbidden_fields(tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    (state / "bad.json").write_text(json.dumps({"target_ir": "x"}), encoding="utf-8")
    scan = scan_state_for_forbidden_fields(state, ["bad.json"])
    assert scan["forbidden_field_in_state_count"] == 1
