from jianmu.self_learning.darwinforge.historical_records_write_audit import audit_historical_records_write_policy


def test_historical_records_write_audit_uses_tmp_path(tmp_path):
    result = audit_historical_records_write_policy(tmp_path)
    assert result["real_historical_records_write_allowed"] is False
    assert result["historical_records_write_audit_passed"] is True


def test_no_write_to_historical_records(tmp_path):
    audit_historical_records_write_policy(tmp_path)
    assert not (tmp_path / "records" / "v0_6_7").exists()
