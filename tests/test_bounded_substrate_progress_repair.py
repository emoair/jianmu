from __future__ import annotations

from jianmu.self_learning.darwinforge.bounded_substrate_progress_repair import run_progress_sanity


def test_progress_repair_emits_many_events_for_quick_run(tmp_path) -> None:
    summary = run_progress_sanity(tmp_path, progress=True, progress_interval_seconds=999, progress_min_samples=50, force_text_progress=True)
    assert summary["progress_events_emitted"] >= 20
    assert summary["progress_metrics_safe"] is True


def test_progress_repair_no_tty_periodic_log(tmp_path) -> None:
    summary = run_progress_sanity(tmp_path, progress=True, force_text_progress=True)
    assert summary["progress_backend"] == "periodic_text"
    assert "[progress]" in (tmp_path / "progress_event_sample.log").read_text(encoding="utf-8")


def test_progress_repair_disabled_emits_zero_events(tmp_path) -> None:
    summary = run_progress_sanity(tmp_path, progress=False)
    assert summary["progress_events_emitted"] == 0


def test_progress_repair_does_not_modify_metrics(tmp_path) -> None:
    summary = run_progress_sanity(tmp_path, progress=True)
    assert summary["metrics_affected_by_progress"] is False

