from jianmu.self_learning.darwinforge.windows_onedrive_records_isolation import audit_windows_onedrive_records_isolation


def test_windows_onedrive_records_isolation_blocks_real_records_write(tmp_path):
    result = audit_windows_onedrive_records_isolation(tmp_path, tmp_path / "OneDrive" / "repo")
    assert result["tests_write_real_records_detected"] is False
    assert result["windows_onedrive_isolation_passed"] is True
