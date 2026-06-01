from jianmu.self_learning.darwinforge.freeze_candidate_risk_register import run_risk_register


def test_risk_register_contains_core_risks(tmp_path):
    register = run_risk_register(tmp_path)
    names = {row["risk"] for row in register["risks"]}
    assert "overclaim risk" in names
    assert "human-review missing risk" in names
    assert register["risk_register_completed"] is True
