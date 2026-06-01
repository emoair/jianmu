from __future__ import annotations

from jianmu.self_learning.darwinforge.codecartographer_dataset_builder import build_row
from jianmu.self_learning.darwinforge.codecartographer_token_to_ir_adapter import standard_token_to_ir


def test_codecartographer_token_to_ir_adapter():
    row = build_row("m", "int compute(void) { int x = 1; return x; }", "row_001", "train")
    ir = standard_token_to_ir(row)
    assert ir["op"] == "Program"
    assert row["project_standard_token"]["reversible_to_ir"] is True
