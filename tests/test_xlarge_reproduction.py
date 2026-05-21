from pathlib import Path

from jianmu.self_learning.darwinforge.xlarge_reproduction import (
    add_lifecycle_cumulative_metrics,
    build_guard_metric_record,
    summarize_reproduction,
)


def test_xlarge_reproduction_summary_requires_same_and_alt_seed():
    runs = [
        {"name": "xlarge_same_seed", "completed": True, "global_correct_targetir_in_beam_rate": 0.82, "candidate_space_failure_rate": 0.18, "ood_false_accept_rate": 0.335},
        {"name": "xlarge_light_alt_seed", "completed": False, "global_correct_targetir_in_beam_rate": None, "candidate_space_failure_rate": None, "ood_false_accept_rate": None},
    ]
    result = summarize_reproduction(runs, pytest_green=True, metric_consistency_passed=True)
    assert result["same_seed_completed"] is True
    assert result["alt_seed_completed"] is False
    assert result["reproduced_strong_signal"] is False


def test_reproduced_strong_signal_requires_pytest_green():
    runs = [
        {"name": "xlarge_same_seed", "completed": True, "global_correct_targetir_in_beam_rate": 0.82, "candidate_space_failure_rate": 0.18, "ood_false_accept_rate": 0.335},
        {"name": "xlarge_light_alt_seed", "completed": True, "global_correct_targetir_in_beam_rate": 0.72, "candidate_space_failure_rate": 0.28, "ood_false_accept_rate": 0.335},
    ]
    assert summarize_reproduction(runs, pytest_green=False, metric_consistency_passed=True)["reproduced_strong_signal"] is False


def test_guard_metric_records_baseline_mode():
    row = build_guard_metric_record({"mode": "xlarge", "run_id": "r1", "global_correct_targetir_in_beam_rate": 0.8167, "ood_false_accept_after_shadow": 0.335})
    assert row["baseline_mode"] == "xlarge"
    assert row["baseline_global_beam"] == 0.8167
    assert row["after_guard_global_beam"] == 0.8167


def test_nourished_cumulative_events_reported():
    run = add_lifecycle_cumulative_metrics({"stable_root_count": 4739, "nourished_root_count": 0})
    assert run["final_nourished_root_count"] == 0
    assert run["cumulative_nourished_event_count"] >= 4739


def test_mainline_conclusion_ledger_exists():
    expected = Path("records/v0_8_1_1/mainline_conclusion.md")
    assert expected.as_posix().endswith("mainline_conclusion.md")
