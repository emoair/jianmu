from __future__ import annotations

import json
from pathlib import Path

from jianmu.self_learning.darwinforge.forgefrontier_eval import evaluate_forgefrontier
from jianmu.self_learning.darwinforge.forgefrontier_function_array_generator import generate_forgefrontier_dataset
from jianmu.self_learning.darwinforge.ironjudge_checkpoint import checkpoint_roundtrip, load_checkpoint
from jianmu.self_learning.darwinforge.ironjudge_invocation_accounting import build_invocation_accounting
from jianmu.self_learning.darwinforge.ironjudge_resumable_runner import run_ironjudge_resumable_scaleup
from jianmu.self_learning.darwinforge.ironjudge_resume_manifest import load_v0_9_18_resume_manifest
from jianmu.self_learning.darwinforge.ironjudge_sample_planner import plan_ironjudge_samples
from jianmu.self_learning.darwinforge.ironjudge_scaleup_failure_taxonomy import write_failure_taxonomy


GROUPS = [
    "bounded_control_baseline_v0_9_17",
    "pure_function_frontier_only",
    "fixed_array_frontier_only",
    "function_control_frontier",
    "array_loop_frontier",
    "function_array_combined_frontier",
    "forgefrontier_redqueen_hydra_combined",
]


def _source_records(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    source.mkdir()
    trace = [{"sample_id_hash": "prev_hash", "compiler_invoked": True, "compiler_verified_correct": True, "compile_success": True, "runtime_success": True}]
    (source / "ironjudge_trace_000.jsonl").write_text("".join(json.dumps(row) + "\n" for row in trace), encoding="utf-8")
    (source / "ironjudge_trace_manifest.json").write_text(json.dumps({"shards": [{"path": "ironjudge_trace_000.jsonl", "row_count": 1}], "total_rows": 1}), encoding="utf-8")
    (source / "ironjudge_scale_validation.json").write_text(json.dumps({"ironjudge_invocation_count": 1}), encoding="utf-8")
    evaluate_forgefrontier(source, GROUPS, ["quick"])
    (source / "forgefrontier_readiness.json").write_text(json.dumps({"bounded_control_preserved": True}), encoding="utf-8")
    return source


def _dataset(tmp_path: Path) -> Path:
    generate_forgefrontier_dataset(tmp_path / "ff", tmp_path / "records", scales=["pilot"], scale_totals={"pilot": 200}, shard_size=100)
    return tmp_path / "ff"


def test_ironjudge_checkpoint_roundtrip(tmp_path: Path) -> None:
    checkpoint = checkpoint_roundtrip(tmp_path)
    loaded = load_checkpoint(tmp_path, "gate_5k")
    assert loaded == checkpoint
    assert loaded["resume_safe"] is True


def test_ironjudge_resume_manifest_loads_v0_9_18(tmp_path: Path) -> None:
    source = _source_records(tmp_path)
    manifest = load_v0_9_18_resume_manifest(source)
    assert manifest["resume_from_v0_9_18"] is True
    assert len(manifest["previous_valid_traces"]) == 1


def test_ironjudge_sample_planner_no_duplicate_hashes(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path)
    plan = plan_ironjudge_samples(dataset, [], 50)
    hashes = [row["sample_id_hash"] for row in plan["planned_rows"]]
    assert len(hashes) == len(set(hashes))


def test_ironjudge_invocation_accounting_no_cached_as_new(tmp_path: Path) -> None:
    accounting = build_invocation_accounting(tmp_path, 3, 0, [{"sample_id_hash": "a", "compiler_invoked": True}])
    assert accounting["cached_result_used_as_new_count"] == 0
    assert accounting["total_accounted_invocation_count"] == 4


def test_ironjudge_resumable_runner_levels(tmp_path: Path) -> None:
    result = run_ironjudge_resumable_scaleup(_source_records(tmp_path), _dataset(tmp_path), tmp_path / "out", ["gate_5k"], target_gate=2, target_main=3, target_extended=4, compile_worker_count=1, max_runtime_hours=0.01)
    assert result["readiness"]["resume_from_v0_9_18"] is True
    assert result["scaleup"]["levels"][0]["completed_invocations"] >= 2


def test_ironjudge_failure_taxonomy_categories(tmp_path: Path) -> None:
    taxonomy = write_failure_taxonomy(tmp_path, [{"sample_id_hash": "x", "compiler_invoked": True, "compiler_verified_correct": False, "timeout": True}])
    assert taxonomy["failure_category_distribution"]["runtime_timeout"] == 1


def test_ironjudge_readiness_claim_levels(tmp_path: Path) -> None:
    result = run_ironjudge_resumable_scaleup(_source_records(tmp_path), _dataset(tmp_path), tmp_path / "out", ["gate_5k"], target_gate=2, target_main=3, target_extended=4, compile_worker_count=1, max_runtime_hours=0.01)
    assert "turing" not in result["readiness"]["recommended_claim_level"].lower()
    assert "Turing completeness" in result["mainline"]["still_not_proven"]


def test_integrity_original_v0_9_18_preserved(tmp_path: Path) -> None:
    result = run_ironjudge_resumable_scaleup(_source_records(tmp_path), _dataset(tmp_path), tmp_path / "out", ["gate_5k"], target_gate=2, target_main=3, target_extended=4, compile_worker_count=1, max_runtime_hours=0.01)
    assert result["integrity"]["original_v0_9_18_records_preserved"] is True


def test_no_expression_oracle_import() -> None:
    for path in Path("jianmu/self_learning/darwinforge").glob("ironjudge_*scaleup*.py"):
        assert "expression_oracle" not in path.read_text(encoding="utf-8")
    for path in Path("jianmu/self_learning/darwinforge").glob("ironjudge_resume*.py"):
        assert "expression_oracle" not in path.read_text(encoding="utf-8")


def test_no_external_api_calls() -> None:
    for path in Path("jianmu/self_learning/darwinforge").glob("ironjudge_*scaleup*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert "requests." not in text
        assert "urllib" not in text
        assert "openai" not in text


def test_no_hardcoded_keyword_gate() -> None:
    for path in Path("jianmu/self_learning/darwinforge").glob("ironjudge_*scaleup*.py"):
        assert "keyword gate" not in path.read_text(encoding="utf-8").lower()


def test_real_promotion_disabled(tmp_path: Path) -> None:
    result = run_ironjudge_resumable_scaleup(_source_records(tmp_path), _dataset(tmp_path), tmp_path / "out", ["gate_5k"], target_gate=2, target_main=3, target_extended=4, compile_worker_count=1, max_runtime_hours=0.01)
    assert result["integrity"]["real_promotion_enabled"] is False
