from pathlib import Path

from jianmu.self_learning.darwinforge.compiler_subprocess_evidence import sha256_file


def test_compiler_subprocess_evidence_hashes_source(tmp_path: Path) -> None:
    p = tmp_path / "a.c"
    p.write_text("int main(void){return 0;}", encoding="utf-8")
    assert len(sha256_file(p)) == 64

