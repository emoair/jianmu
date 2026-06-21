from jianmu.self_learning.darwinforge.redqueen_endurance_report import write_endurance_report


def test_redqueen_endurance_report(tmp_path):
    write_endurance_report(tmp_path, {"recommended_claim_level": "redqueen_real_landing_endurance_positive", "redqueen_autonomous_governance_completed": False})
    assert (tmp_path / "mainline_conclusion.md").exists()


def test_no_expression_oracle_import():
    import pathlib
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("redqueen_*landing*.py"))
    assert "expression_oracle" not in text


def test_no_external_api_calls():
    import pathlib
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("redqueen_*landing*.py"))
    assert "openai" not in text
    assert "requests." not in text


def test_real_promotion_disabled():
    import pathlib
    text = pathlib.Path("jianmu/self_learning/darwinforge/redqueen_real_landing_readiness.py").read_text(encoding="utf-8")
    assert '"real_promotion_enabled": True' not in text
