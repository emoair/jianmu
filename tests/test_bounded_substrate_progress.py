from __future__ import annotations

import io

from jianmu.self_learning.darwinforge.bounded_substrate_progress import ProgressReporter


def test_bounded_substrate_progress_disabled_has_no_output() -> None:
    stream = io.StringIO()
    reporter = ProgressReporter(enabled=False, stream=stream)
    reporter.update(mode="quick", phase="train", processed=1, total=2, force=True)
    assert stream.getvalue() == ""
    assert reporter.summary()["progress_events_emitted"] == 0


def test_bounded_substrate_progress_enabled_emits_progress() -> None:
    stream = io.StringIO()
    reporter = ProgressReporter(enabled=True, stream=stream, interval_seconds=0)
    reporter.update(mode="quick", phase="train", processed=1, total=2, force=True)
    assert "[progress]" in stream.getvalue()
    assert reporter.summary()["progress_events_emitted"] == 1


def test_bounded_substrate_progress_no_tty_fallback() -> None:
    stream = io.StringIO()
    reporter = ProgressReporter(enabled=True, stream=stream)
    assert reporter.summary()["progress_backend"] == "periodic_text"


def test_bounded_substrate_progress_does_not_modify_metrics() -> None:
    metrics = {"top1": 0.5}
    stream = io.StringIO()
    reporter = ProgressReporter(enabled=True, stream=stream, interval_seconds=0)
    reporter.update(mode="quick", phase="eval", processed=2, total=2, force=True, metrics=metrics)
    assert metrics == {"top1": 0.5}
    assert reporter.summary()["metrics_affected_by_progress"] is False

