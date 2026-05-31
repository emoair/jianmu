from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.forgefrontier_array_grammar import fixed_array_spec
from jianmu.self_learning.darwinforge.forgefrontier_compiler_validation import render_forgefrontier_c_source, run_forgefrontier_compiler_validation
from jianmu.self_learning.darwinforge.forgefrontier_eval import evaluate_forgefrontier
from jianmu.self_learning.darwinforge.forgefrontier_frontier_audit import audit_rows
from jianmu.self_learning.darwinforge.forgefrontier_function_array_generator import generate_forgefrontier_dataset, iter_forgefrontier_rows, make_forgefrontier_sample
from jianmu.self_learning.darwinforge.forgefrontier_function_grammar import pure_function_spec
from jianmu.self_learning.darwinforge.forgefrontier_probe import run_forgefrontier_ironjudge_probe
from jianmu.self_learning.darwinforge.forgefrontier_target_ir import make_frontier_target_ir
from jianmu.self_learning.darwinforge.ironjudge_compiler_scale_validation import run_ironjudge_scale_validation


GROUPS = [
    "bounded_control_baseline_v0_9_17",
    "pure_function_frontier_only",
    "fixed_array_frontier_only",
    "function_control_frontier",
    "array_loop_frontier",
    "function_array_combined_frontier",
    "forgefrontier_redqueen_hydra_combined",
]


def _redqueen_dataset(tmp_path: Path) -> Path:
    from jianmu.self_learning.darwinforge.redqueen_failure_miner import mine_redqueen_failures
    from jianmu.self_learning.darwinforge.redqueen_curriculum_generator import generate_redqueen_curriculum

    failure = mine_redqueen_failures(tmp_path / "source", tmp_path / "records")
    generate_redqueen_curriculum(tmp_path / "redqueen", tmp_path / "records", failure, scales=["pilot"], scale_totals={"pilot": 20}, shard_size=20)
    return tmp_path / "redqueen"


def _frontier_dataset(tmp_path: Path) -> Path:
    generate_forgefrontier_dataset(tmp_path / "ff", tmp_path / "records", scales=["pilot"], scale_totals={"pilot": 100}, shard_size=50)
    return tmp_path / "ff"


def test_ironjudge_real_compiler_invocation_levels(tmp_path: Path) -> None:
    rq = _redqueen_dataset(tmp_path)
    result = run_ironjudge_scale_validation(tmp_path / "source", rq, tmp_path / "records", ["gate_5k"], compile_worker_count=1, per_level_runtime_cap_seconds=0.01)
    assert result["ironjudge_invocation_count"] >= 1
    assert result["ironjudge_levels"][0]["target_invocations"] == 5000


def test_ironjudge_does_not_use_cached_results(tmp_path: Path) -> None:
    rq = _redqueen_dataset(tmp_path)
    result = run_ironjudge_scale_validation(tmp_path / "source", rq, tmp_path / "records", ["gate_5k"], compile_worker_count=1, per_level_runtime_cap_seconds=0.01)
    assert (tmp_path / "records" / "ironjudge_trace_manifest.json").exists()
    assert result["backend_type"] == "real_c_compiler"


def test_forgefrontier_function_no_recursion() -> None:
    spec = pure_function_spec()
    assert spec["has_function"] is True
    assert spec["has_recursion"] is False


def test_forgefrontier_array_no_pointer() -> None:
    spec = fixed_array_spec()
    assert spec["has_array"] is True
    assert spec["has_pointer"] is False
    assert spec["array_index_static_safe"] is True


def test_forgefrontier_blocks_recursion_pointer_io() -> None:
    rows = [make_forgefrontier_sample(80, "pilot"), make_forgefrontier_sample(85, "pilot"), make_forgefrontier_sample(90, "pilot")]
    audit = audit_rows(rows)
    assert audit["recursion_experimental_supported_count"] == 0
    assert audit["pointer_experimental_supported_count"] == 0
    assert audit["io_experimental_supported_count"] == 0


def test_forgefrontier_schema_support_status(tmp_path: Path) -> None:
    dataset = _frontier_dataset(tmp_path)
    row = next(iter_forgefrontier_rows(dataset / "pilot"))
    assert row["support_status"].startswith("experimental_supported")
    assert row["expected_action"] == "train_experimental"


def test_forgefrontier_target_ir_not_c_source() -> None:
    target = make_frontier_target_ir("forge_function", 7)
    assert target["stdout"] == 7
    assert "int main" not in str(target)


def test_forgefrontier_compiler_validation_uses_real_cl(tmp_path: Path) -> None:
    dataset = _frontier_dataset(tmp_path)
    result = run_forgefrontier_compiler_validation(dataset, tmp_path / "records", function_spot=1, array_spot=1, function_array_spot=1, boundary_spot=1, compile_worker_count=1)
    assert result["compiler_name"] == "cl"
    assert result["backend_type"] == "real_c_compiler"


def test_function_array_frontier_metrics_separate_from_current_supported(tmp_path: Path) -> None:
    result = evaluate_forgefrontier(tmp_path / "records", GROUPS, ["quick"])
    best = max(result["runs"], key=lambda row: row["experimental_frontier_success_rate"])
    assert "top1_bounded_control" in best
    assert "top1_function_frontier" in best


def test_bounded_control_preservation_gate(tmp_path: Path) -> None:
    rq = _redqueen_dataset(tmp_path)
    result = run_forgefrontier_ironjudge_probe(tmp_path / "v2", tmp_path / "zh", rq, tmp_path / "source", tmp_path / "records", tmp_path / "ff", GROUPS, ["gate_5k"], compile_worker_count=1, run_compiler_validation=False, forgefrontier_scale_totals={"pilot": 100, "medium": 100, "large": 100}, ironjudge_runtime_cap_seconds=0.01)
    assert result["readiness"]["bounded_control_preserved"] is True


def test_frontier_readiness_no_turing_claim(tmp_path: Path) -> None:
    rq = _redqueen_dataset(tmp_path)
    result = run_forgefrontier_ironjudge_probe(tmp_path / "v2", tmp_path / "zh", rq, tmp_path / "source", tmp_path / "records", tmp_path / "ff", GROUPS, ["gate_5k"], compile_worker_count=1, run_compiler_validation=False, forgefrontier_scale_totals={"pilot": 100, "medium": 100, "large": 100}, ironjudge_runtime_cap_seconds=0.01)
    assert "turing" not in result["readiness"]["recommended_claim_level"].lower()
    assert "Turing completeness" in result["mainline"]["still_not_proven"]


def test_no_expression_oracle_import() -> None:
    for path in Path("jianmu/self_learning/darwinforge").glob("*forgefrontier*.py"):
        assert "expression_oracle" not in path.read_text(encoding="utf-8")
    for path in Path("jianmu/self_learning/darwinforge").glob("*ironjudge*.py"):
        assert "expression_oracle" not in path.read_text(encoding="utf-8")


def test_no_external_api_calls() -> None:
    for pattern in ["*forgefrontier*.py", "*ironjudge*.py"]:
        for path in Path("jianmu/self_learning/darwinforge").glob(pattern):
            text = path.read_text(encoding="utf-8").lower()
            assert "requests." not in text
            assert "urllib" not in text
            assert "openai" not in text


def test_no_hardcoded_keyword_gate() -> None:
    for pattern in ["*forgefrontier*.py", "*ironjudge*.py"]:
        for path in Path("jianmu/self_learning/darwinforge").glob(pattern):
            assert "keyword gate" not in path.read_text(encoding="utf-8").lower()


def test_real_promotion_disabled(tmp_path: Path) -> None:
    rq = _redqueen_dataset(tmp_path)
    result = run_forgefrontier_ironjudge_probe(tmp_path / "v2", tmp_path / "zh", rq, tmp_path / "source", tmp_path / "records", tmp_path / "ff", GROUPS, ["gate_5k"], compile_worker_count=1, run_compiler_validation=False, forgefrontier_scale_totals={"pilot": 100, "medium": 100, "large": 100}, ironjudge_runtime_cap_seconds=0.01)
    assert result["integrity"]["real_promotion_enabled"] is False
