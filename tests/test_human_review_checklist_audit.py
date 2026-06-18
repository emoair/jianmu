from jianmu.self_learning.darwinforge.human_review_checklist_audit import REQUIRED_REVIEWER_FILES, audit_reviewer_pack


def test_reviewer_pack_audit_requires_all_files(tmp_path):
    source = tmp_path / "source"
    pack = source / "reviewer_support_pack"
    pack.mkdir(parents=True)
    for name in REQUIRED_REVIEWER_FILES:
        (pack / name).write_text("{}" if name.endswith(".json") else "does not prove production readiness", encoding="utf-8")
    result = audit_reviewer_pack(source, tmp_path / "out")
    assert result["reviewer_pack_audit_passed"] is True
