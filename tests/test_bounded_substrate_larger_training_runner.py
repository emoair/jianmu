from __future__ import annotations

import json
from pathlib import Path

from jianmu.self_learning.darwinforge import bounded_substrate_larger_training_runner as larger


def _program(value: int = 1) -> dict:
    return {
        "op": "Program",
        "body": [
            {"op": "VarDecl", "name": "x", "value": {"op": "Int", "value": value}},
            {"op": "Print", "value": {"op": "Var", "name": "x"}},
        ],
    }


def _row(idx: int, category: str = "current_supported_turing_substrate", split: str = "train", stage: str = "variable_declaration") -> dict:
    supported = category == "current_supported_turing_substrate"
    return {
        "id": f"{split}-{category}-{idx}",
        "split": split,
        "stage": stage if supported else "boundary_rejection",
        "category": category,
        "input": f"program {idx}",
        "canonical_program": f"print {idx}",
        "target_ir": _program(idx % 7 + 1) if supported else None,
        "expected_output": str(idx % 7 + 1) if supported else None,
        "expected_type": "int_stdout" if supported else "unsupported",
        "training_usage": "train_current" if supported and split == "train" else "eval_current",
        "language_features": {},
        "complexity": {},
        "nutrient_policy": {"supported_correct": 1.0},
        "toxicity_policy": {"false_accept_toxic": 1.0},
    }


def _write_dataset(root: Path) -> None:
    for scale in ["small", "medium", "large"]:
        for split in ["train", "eval", "test", "heldout"]:
            d = root / scale / split
            d.mkdir(parents=True, exist_ok=True)
            rows = [_row(i, split=split, stage=stage) for i, stage in enumerate(larger.base_runner.SUPPORTED_STAGES if hasattr(larger.base_runner, "SUPPORTED_STAGES") else ["variable_declaration"])]
            rows += [_row(100 + i, category="unsupported_program_boundary", split=split) for i in range(3)]
            (d / "data.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_bounded_substrate_larger_runner_quick(tmp_path) -> None:
    dataset = tmp_path / "dataset"
    _write_dataset(dataset)
    out = tmp_path / "records"
    metrics = larger.run_bounded_substrate_larger_training_rerun(
        dataset,
        tmp_path / "source",
        out,
        ["quick"],
        [63],
        run_cross_process=False,
        run_compiler_validation=False,
        progress=False,
    )
    assert metrics["supported_candidate_hit_after"] >= metrics["supported_candidate_hit_before"]
    assert (out / "bounded_substrate_larger_training_metrics.json").exists()
    assert json.loads((out / "progress_summary.json").read_text(encoding="utf-8"))["metrics_affected_by_progress"] is False


def test_bounded_substrate_larger_runner_marks_partial_correctly(tmp_path) -> None:
    dataset = tmp_path / "dataset"
    _write_dataset(dataset)
    metrics = larger.run_bounded_substrate_larger_training_rerun(
        dataset,
        tmp_path / "source",
        tmp_path / "records",
        ["quick"],
        [63],
        run_cross_process=False,
        run_compiler_validation=False,
        progress=False,
        max_runtime_hours=0,
    )
    assert metrics["larger_rerun_partial"] is True


def test_bounded_substrate_larger_uses_clean_temp_manager(monkeypatch, tmp_path) -> None:
    dataset = tmp_path / "dataset"
    _write_dataset(dataset)
    called = {"value": False}

    def fake_clean_validation(*args, **kwargs):
        called["value"] = True
        out = Path(args[1])
        (out / "independent_validation_trace_primary_16.jsonl").write_text("", encoding="utf-8")
        (out / "independent_validation_trace_manifest.json").write_text(json.dumps({"shards": []}), encoding="utf-8")
        return {"primary": {"completed": True, "backend_type": "real_c_compiler", "compiler_name": "cl", "compiler_environment": "msvc_vcvars64", "real_compiler_invocation_count": 1, "compiler_verified_correct_rate": 1.0, "permission_error_count": 0, "cleanup_failure_count": 0, "boundary_compiler_misroute_count": 0, "backend_claim_safe": True}}

    monkeypatch.setattr(larger, "run_clean_independent_validation", fake_clean_validation)
    larger.run_bounded_substrate_larger_training_rerun(dataset, tmp_path / "source", tmp_path / "records", ["quick"], [63], run_cross_process=False, run_compiler_validation=True, progress=False)
    assert called["value"] is True


def test_bounded_substrate_larger_compiler_validation_uses_real_cl(monkeypatch, tmp_path) -> None:
    dataset = tmp_path / "dataset"
    _write_dataset(dataset)

    def fake_clean_validation(*args, **kwargs):
        out = Path(args[1])
        (out / "independent_validation_trace_primary_16.jsonl").write_text("", encoding="utf-8")
        (out / "independent_validation_trace_manifest.json").write_text(json.dumps({"shards": []}), encoding="utf-8")
        return {"primary": {"completed": True, "backend_type": "real_c_compiler", "compiler_name": "cl", "compiler_environment": "msvc_vcvars64", "compile_worker_count": 16, "real_compiler_invocation_count": 1, "compiler_verified_correct_rate": 1.0, "permission_error_count": 0, "cleanup_failure_count": 0, "boundary_compiler_misroute_count": 0, "backend_claim_safe": True}}

    monkeypatch.setattr(larger, "run_clean_independent_validation", fake_clean_validation)
    metrics = larger.run_bounded_substrate_larger_training_rerun(dataset, tmp_path / "source", tmp_path / "records", ["quick"], [63], run_cross_process=False, run_compiler_validation=True, progress=False)
    assert metrics["backend_type"] == "real_c_compiler"
    assert metrics["compiler_name"] == "cl"

