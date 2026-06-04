from __future__ import annotations

from jianmu.self_learning.darwinforge.project_dataset_builder import build_project_row


def test_project_dataset_builder_unsupported_has_no_target() -> None:
    row = build_project_row("pilot", 95)
    assert row["support_status"] == "unsupported"
    assert row["target_ir"] is None
    assert row["expected_output"] is None

