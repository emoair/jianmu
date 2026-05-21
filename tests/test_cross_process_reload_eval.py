from jianmu.self_learning.darwinforge.cross_process_reload_eval import run_cross_process_reload_eval
from jianmu.self_learning.darwinforge.full_state_serializer import save_full_state


def test_cross_process_reload_uses_new_process(tmp_path):
    records = tmp_path / "records"
    records.mkdir()
    save_full_state(records, tmp_path / "state")
    result = run_cross_process_reload_eval(tmp_path / "state", "datasets/v0_8_5_boundary_aware", tmp_path / "out", mode="quick")
    assert result["used_new_process"] is True


def test_cross_process_reload_no_forbidden_fields(tmp_path):
    records = tmp_path / "records"
    records.mkdir()
    save_full_state(records, tmp_path / "state")
    result = run_cross_process_reload_eval(tmp_path / "state", "datasets/v0_8_5_boundary_aware", tmp_path / "out", mode="quick")
    assert result["forbidden_field_access_count"] == 0
