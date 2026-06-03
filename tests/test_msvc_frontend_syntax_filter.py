from jianmu.self_learning.darwinforge.msvc_frontend_syntax_filter import run_msvc_frontend_syntax_filter


def test_msvc_frontend_zs_syntax_filter(tmp_path):
    result = run_msvc_frontend_syntax_filter(tmp_path, target=4, batch_size=2)
    assert result["syntax_frontend_enabled"] is True
    assert "/Zs" in result["syntax_frontend_command"]
    assert result["syntax_frontend_checked_count"] == 4
    assert result["syntax_frontend_pass_count"] == 4


def test_syntax_filter_not_correctness_evidence(tmp_path):
    result = run_msvc_frontend_syntax_filter(tmp_path, target=2, batch_size=2)
    assert result["syntax_filter_used_as_correctness_evidence"] is False
