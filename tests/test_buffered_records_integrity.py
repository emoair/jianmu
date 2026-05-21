from jianmu.self_learning.runtime.buffered_records_integrity import check_buffered_records_integrity


def test_buffered_records_integrity_detects_duplicates():
    result = check_buffered_records_integrity([{"sample_id": "a"}, {"sample_id": "a"}], ["a"])
    assert result["duplicate_record_count"] == 1
    assert not result["merge_integrity_passed"]


def test_buffered_records_integrity_detects_missing_records():
    result = check_buffered_records_integrity([{"sample_id": "a"}], ["a", "b"])
    assert result["missing_record_count"] == 1
    assert not result["merge_integrity_passed"]

