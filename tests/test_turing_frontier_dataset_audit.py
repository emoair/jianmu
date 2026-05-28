from __future__ import annotations

import json

from jianmu.self_learning.darwinforge.turing_frontier_dataset_audit import audit_turing_frontier_dataset
from jianmu.self_learning.darwinforge.turing_frontier_generator import generate_turing_frontier_dataset


def test_turing_frontier_dataset_audit_blocks_future_targets(monkeypatch, tmp_path) -> None:
    import jianmu.self_learning.darwinforge.turing_frontier_generator as gen

    monkeypatch.setitem(gen.SCALE_TOTALS, "small", 100)
    root = tmp_path / "dataset"
    generate_turing_frontier_dataset(root, tmp_path / "records", ["small"], 68, 50)
    path = next((root / "small").glob("*/data_*.jsonl"))
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    rows[0]["category"] = "future_function_candidate"
    rows[0]["target_ir"] = {"op": "Program"}
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    result = audit_turing_frontier_dataset(root, tmp_path / "records", ["small"])
    assert result["by_scale"]["small"]["non_supported_has_targetir_count"] >= 1
    assert result["audit_passed_by_scale"]["small"] is False

