from pathlib import Path

from jianmu.self_learning.darwinforge.archive_index_builder import build_archive_index


def test_archive_index_generated(tmp_path: Path) -> None:
    payload = build_archive_index(Path.cwd(), tmp_path)
    assert payload["archive_index_generated"] is True
    assert any("v0.9.28" in item[0] for item in payload["evidence_archive"])
    assert "records/v0_9_28_1/full_compile_50k_accounting.json" in payload["critical_records_to_preserve"]


def test_records_and_dataset_archive_indexes(tmp_path: Path) -> None:
    payload = build_archive_index(Path.cwd(), tmp_path)
    assert payload["records_archive_index"]
    assert isinstance(payload["dataset_archive_index"], list)
    assert payload["checksum_needed"] is True
