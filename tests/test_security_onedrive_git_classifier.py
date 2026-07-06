from jianmu.self_learning.darwinforge.security_onedrive_git_classifier import classify_process, classify_process_rows


def test_security_onedrive_git_classifier_detects_known_names() -> None:
    assert classify_process("OneDrive.exe") == "onedrive"
    assert classify_process("MsMpEng.exe") == "defender"
    result = classify_process_rows([{"name": "git.exe", "cmdline": "git status"}])
    assert result["git_activity_detected"] is True
