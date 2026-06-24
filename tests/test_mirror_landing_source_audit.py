from jianmu.self_learning.darwinforge.mirror_landing_source_audit import audit_mirror_landing_source


def test_mirror_source_audit_detects_docs_only_claim(tmp_path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "records").mkdir()
    (tmp_path / "jianmu").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "examples").mkdir()
    (tmp_path / "docs" / "claim.md").write_text("mirror alternating freeze claim\n", encoding="utf-8")
    result = audit_mirror_landing_source(tmp_path / "out", tmp_path)
    assert result["mirror_docs_only_detected"] is True
    assert result["landing_status"] == "docs_or_records_only"

