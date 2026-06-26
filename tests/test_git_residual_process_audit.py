from jianmu.self_learning.darwinforge.git_residual_process_audit import classify_git_root_cause


def test_git_residual_process_audit_classifies_git_storm() -> None:
    result = classify_git_root_cause([{"CommandLine": "git.exe ls-files --others --exclude-standard"}], 0, 0)
    assert result == "ide_git_integration"
