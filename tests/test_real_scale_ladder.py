from jianmu.self_learning.darwinforge.real_scale_ladder import run_real_scale_ladder, summarize_real_scale_ladder


def test_real_scale_ladder_runs_independent_scales():
    rows = run_real_scale_ladder(lambda cfg: {"global_correct_targetir_in_beam_rate": 0.1, "ood_false_accept_rate": 0.0}, skip_levels=["large"])

    actual = [row for row in rows if not row["skipped"]]
    assert len(actual) == 2
    assert actual[0]["run_id"] != actual[1]["run_id"]
    assert actual[0]["scale_label"] == "small"
    assert actual[1]["scale_label"] == "medium"


def test_real_scale_ladder_records_run_id():
    rows = run_real_scale_ladder(lambda cfg: {}, skip_levels=["medium", "large"])

    assert rows[0]["run_id"]
    assert rows[1]["skip_reason"]


def test_ood_guard_applies_to_scale_ladder():
    rows = run_real_scale_ladder(lambda cfg: {"guard_state": "ood_guard_applied", "ood_false_accept_rate": 0.0}, skip_levels=["medium", "large"])

    assert rows[0]["guard_state"] == "ood_guard_applied"


def test_real_scale_ladder_summary_assimilation_effect():
    summary = summarize_real_scale_ladder([], before_rate=0.1, after_rate=0.2)

    assert summary["assimilation_effect_likely"] is True
