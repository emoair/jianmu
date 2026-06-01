from jianmu.self_learning.darwinforge.large_file_hygiene import run_large_file_hygiene


def test_large_file_hygiene_detects_over_45mb(tmp_path):
    big = tmp_path / "big.bin"
    with big.open("wb") as handle:
        handle.seek(46 * 1024 * 1024)
        handle.write(b"0")
    out = tmp_path / "records"
    result = run_large_file_hygiene(out, root=tmp_path)
    assert result["files_over_45mb"]
    assert result["large_file_hygiene_passed"] is True
