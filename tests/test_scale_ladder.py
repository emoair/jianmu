from jianmu.self_learning.darwinforge.scale_ladder import run_scale_ladder, summarize_scale_ladder


def test_scale_ladder_outputs_three_levels_or_skip_reason():
    rows = run_scale_ladder(
        lambda config: {"correct_targetir_in_beam_rate": 0.0, "subbeam_rescue_rate": 0.0},
        skip_levels=["large"],
    )

    assert [row["scale"] for row in rows] == ["small", "medium", "large"]
    assert rows[-1]["skipped"] is True
    assert rows[-1]["skip_reason"]


def test_scale_ladder_classifies_scale_limited_or_structural():
    rows = [
        {"scale": "small", "skipped": False, "correct_targetir_in_beam_rate": 0.0, "subbeam_rescue_rate": 0.0},
        {"scale": "medium", "skipped": False, "correct_targetir_in_beam_rate": 0.1, "subbeam_rescue_rate": 0.0},
        {"scale": "large", "skipped": True, "skip_reason": "bounded"},
    ]

    summary = summarize_scale_ladder(rows)

    assert summary["scale_limited_likely"] is True
    assert summary["structural_failure_likely"] is False
