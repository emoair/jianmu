import json
from pathlib import Path

from jianmu.self_learning.darwinforge.arithmetic_training_runner import run_arithmetic_training_probe


def _row(i, split, category="current_supported_arithmetic", stage="single_op", division_kind="none"):
    supported = category == "current_supported_arithmetic"
    return {
        "id": f"{split}-{category}-{i}",
        "split": split,
        "stage": stage,
        "category": category,
        "input": f"{i}+1",
        "canonical_expression": f"{i}+1" if supported else None,
        "target_ir": {"op": "add", "args": [{"op": "int", "value": i}, {"op": "int", "value": 1}]} if supported else None,
        "expected_output": f"{i + 1}\n" if supported else None,
        "expected_type": "int" if supported else "unsupported",
        "boundary_label": "current_supported" if supported else category,
        "expected_action": "accept_supported" if supported else "reject",
        "nutrient_policy": {},
        "toxicity_policy": {},
        "division_kind": division_kind,
        "provenance": {"generation_rule": stage},
    }


def _write_dataset(root: Path):
    for split in ["train", "eval", "test", "heldout"]:
        split_dir = root / "small" / split
        split_dir.mkdir(parents=True, exist_ok=True)
        rows = [_row(i, split, stage="precedence" if i % 2 else "single_op") for i in range(30)]
        rows += [_row(100 + i, split, "unsupported_arithmetic_boundary", "division_boundary", "division_by_zero") for i in range(5)]
        rows += [_row(200 + i, split, "future_domain_candidate", "division_boundary", "non_integer") for i in range(5)]
        (split_dir / f"{split}_000.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_arithmetic_training_runner_quick(tmp_path):
    dataset = tmp_path / "dataset"
    records = tmp_path / "records"
    _write_dataset(dataset)
    result = run_arithmetic_training_probe(dataset, records, ["quick"], seeds=[42], run_cross_process=True)
    summary = result["summary"]
    assert summary["modes_completed"] == ["quick"]
    assert summary["forbidden_field_access_count"] == 0
    assert summary["cross_process_reload_passed"] is True
    assert (records / "arithmetic_training_metrics.json").exists()


def test_arithmetic_cross_process_reload_trace(tmp_path):
    dataset = tmp_path / "dataset"
    records = tmp_path / "records"
    _write_dataset(dataset)
    run_arithmetic_training_probe(dataset, records, ["quick"], seeds=[42], run_cross_process=True)
    trace = json.loads((records / "arithmetic_cross_process_trace.json").read_text(encoding="utf-8"))
    assert trace["subprocess_spawned"] is True
    assert trace["child_eval_sample_count"] > 0


def test_arithmetic_workload_counters(tmp_path):
    dataset = tmp_path / "dataset"
    records = tmp_path / "records"
    _write_dataset(dataset)
    run_arithmetic_training_probe(dataset, records, ["quick"], seeds=[42], run_cross_process=True)
    counters = json.loads((records / "sample_processing_counters.json").read_text(encoding="utf-8"))
    assert counters["actual_train_iterated_count"] > 0
    assert counters["freebeam_eval_call_count"] > 0


def test_mainline_conclusion_ledger_exists(tmp_path):
    dataset = tmp_path / "dataset"
    records = tmp_path / "records"
    _write_dataset(dataset)
    run_arithmetic_training_probe(dataset, records, ["quick"], seeds=[42], run_cross_process=True)
    assert (records / "mainline_conclusion.md").exists()
    assert (records / "mainline_conclusion.json").exists()
