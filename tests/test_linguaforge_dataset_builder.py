from __future__ import annotations

from jianmu.self_learning.darwinforge.linguaforge_dataset_builder import build_linguaforge_row


def test_linguaforge_dataset_builder_future_has_no_target() -> None:
    row = build_linguaforge_row("pilot", 39)
    assert row["support_status"] != "current_supported"
    assert row["target_ir"] is None
    assert row["expected_output"] is None

