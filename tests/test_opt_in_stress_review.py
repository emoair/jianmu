from jianmu.self_learning.darwinforge.opt_in_stress_review import run_opt_in_stress_review


def test_opt_in_stress_review_delegates(tmp_path, monkeypatch):
    monkeypatch.setattr("jianmu.self_learning.darwinforge.opt_in_stress_review.run_opt_in_rollback_audit", lambda *args, **kwargs: {"opt_in_rollback_passed": True})
    assert run_opt_in_stress_review(tmp_path)["opt_in_rollback_passed"] is True
