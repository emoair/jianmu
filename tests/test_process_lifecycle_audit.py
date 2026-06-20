from jianmu.self_learning.darwinforge.process_lifecycle_audit import audit_process_lifecycle


def test_process_lifecycle_audit_finds_popen_call_sites(tmp_path):
    root = tmp_path
    path = root / "jianmu" / "x.py"
    path.parent.mkdir()
    path.write_text("import subprocess\nsubprocess.run(['x'])\n", encoding="utf-8")
    result = audit_process_lifecycle(root, tmp_path / "out")
    assert result["process_lifecycle_audit_completed"] is True
    assert result["popen_call_sites_found"]
