from __future__ import annotations

from jianmu.self_learning.darwinforge.projectcartographer_schema import build_project_row


def test_projectcartographer_schema_controlled_project_row() -> None:
    row = build_project_row("pilot", 0)
    assert row["dataset_version"] == "v1.0.2_projectcartographer"
    assert row["source_language"] == "c_subset"
    assert row["provenance"]["external_api_used"] is False

