from pathlib import Path

from jianmu.self_learning.darwinforge.windows_records_write_isolation_audit import atomic_write_text, run_windows_records_write_isolation_audit


def test_windows_records_write_isolation_uses_tmp_path(tmp_path):
    result = run_windows_records_write_isolation_audit(tmp_path)
    assert result["windows_write_isolation_passed"] is True
    assert result["tmp_path_isolation_required"] is True


def test_windows_records_write_isolation_blocks_historical_records_write(tmp_path):
    result = run_windows_records_write_isolation_audit(tmp_path, ["records/v0_6_7/file.json"])
    assert result["historical_records_write_detected"] is True
    assert result["windows_write_isolation_passed"] is True


def test_atomic_write_does_not_leave_partial_files(tmp_path):
    target = tmp_path / "out.json"
    atomic_write_text(target, '{"ok": true}\n')
    assert target.read_text(encoding="utf-8") == '{"ok": true}\n'
    assert not list(Path(tmp_path).glob("*.tmp"))


def test_concurrent_shard_write_uses_unique_paths(tmp_path):
    atomic_write_text(tmp_path / "shard_001.jsonl", "a\n")
    atomic_write_text(tmp_path / "shard_002.jsonl", "b\n")
    assert (tmp_path / "shard_001.jsonl").read_text() != (tmp_path / "shard_002.jsonl").read_text()
