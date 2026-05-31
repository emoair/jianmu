from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.hydrabudget_allocator import allocate_hydrabudget
from jianmu.self_learning.darwinforge.hydrabudget_layer_monitor import build_hydrabudget_layer_monitor
from jianmu.self_learning.darwinforge.hydrabudget_rollback_guard import evaluate_rollback
from jianmu.self_learning.darwinforge.hydrabudget_threshold_sweep import run_hydrabudget_threshold_sweep
from jianmu.self_learning.darwinforge.redqueen_curriculum_audit import audit_redqueen_curriculum, audit_rows
from jianmu.self_learning.darwinforge.redqueen_curriculum_generator import generate_redqueen_curriculum, iter_redqueen_rows, make_redqueen_sample
from jianmu.self_learning.darwinforge.redqueen_failure_miner import mine_redqueen_failures
from jianmu.self_learning.darwinforge.redqueen_hydrabudget_compiler_validation import run_redqueen_hydrabudget_compiler_validation
from jianmu.self_learning.darwinforge.redqueen_hydrabudget_probe import run_redqueen_hydrabudget_probe


GROUPS = ["baseline_v0_9_16_stage_balanced", "redqueen_curriculum_only", "hydrabudget_only", "redqueen_plus_hydrabudget"]


def _failure(tmp_path: Path):
    return mine_redqueen_failures(tmp_path / "source", tmp_path / "records")


def _dataset(tmp_path: Path):
    failure = _failure(tmp_path)
    generate_redqueen_curriculum(tmp_path / "rq", tmp_path / "records", failure, scales=["pilot"], shard_size=1000, scale_totals={"pilot": 100})
    return tmp_path / "rq"


def _probe(tmp_path: Path, compiler: bool = False):
    return run_redqueen_hydrabudget_probe(
        tmp_path / "source",
        tmp_path / "records",
        tmp_path / "rq",
        GROUPS,
        [0.75],
        [1.5],
        ["quick"],
        compile_worker_count=1,
        run_compiler_validation=compiler,
        redqueen_scale_totals={"pilot": 100, "medium": 100, "large": 100},
    )


def test_redqueen_failure_miner_outputs_data_need_specs(tmp_path: Path) -> None:
    result = _failure(tmp_path)
    assert len(result["data_need_specs"]) == 8
    assert result["data_need_specs"][0]["required_language"] == "zh"
    assert result["data_need_specs"][0]["support_status"] == "current_supported"


def test_redqueen_curriculum_generator_chinese_only(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path)
    row = next(iter_redqueen_rows(dataset / "pilot"))
    assert row["input_language"] == "zh"
    assert row["support_status"] == "current_supported"
    assert len(row["natural_language_variants"]) >= 4


def test_redqueen_curriculum_audit_blocks_future_features(tmp_path: Path) -> None:
    row = make_redqueen_sample(1, "pilot", _failure(tmp_path)["data_need_specs"][0])
    row["language_features"]["has_function"] = True
    audit = audit_rows([row])
    assert audit["function_supported_count"] == 1
    assert audit["audit_passed"] is False


def test_redqueen_curriculum_compiler_verified(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path)
    audit = audit_redqueen_curriculum(dataset, tmp_path / "records", compiler_rate=1.0)
    assert audit["redqueen_audit_passed"] is True


def test_hydrabudget_layer_monitor_metrics(tmp_path: Path) -> None:
    monitor = build_hydrabudget_layer_monitor(tmp_path / "source", tmp_path / "records")
    assert len(monitor["layers"]) >= 12
    assert "utilization_ratio" in monitor["layers"][0]


def test_hydrabudget_allocator_requires_miss_and_safety(tmp_path: Path) -> None:
    monitor = build_hydrabudget_layer_monitor(tmp_path / "source", tmp_path / "records")
    blocked = dict(monitor["layers"][5])
    blocked["boundary_risk_score"] = 1.0
    result = allocate_hydrabudget([blocked], threshold=0.65)
    assert result["expansion_count"] == 0


def test_hydrabudget_threshold_sweep(tmp_path: Path) -> None:
    monitor = build_hydrabudget_layer_monitor(tmp_path / "source", tmp_path / "records")
    sweep = run_hydrabudget_threshold_sweep(tmp_path / "records", monitor, [0.65, 0.75, 0.8, 0.9], [1.5, 2.0])
    assert len(sweep["threshold_sweep"]) == 8
    assert sweep["best"]["expansion_count"] >= 0


def test_hydrabudget_rollback_on_regression() -> None:
    result = evaluate_rollback(0.86, 0.84, 0.08, 0.09)
    assert result["rollback_required"] is True


def test_budget_expansion_safety_gate_detects_bad_route_amplification() -> None:
    result = evaluate_rollback(0.86, 0.861, 0.08, 0.079, bad_route_amplification=True)
    assert "bad_route_amplification" in result["rollback_reasons"]


def test_redqueen_hydrabudget_eval_groups(tmp_path: Path) -> None:
    result = _probe(tmp_path)
    assert result["readiness"]["best_experiment_group"] == "redqueen_plus_hydrabudget"


def test_data_contamination_gate(tmp_path: Path) -> None:
    result = _probe(tmp_path)
    assert result["contamination"]["data_contamination_gate_passed"] is True
    assert result["integrity"]["train_current_non_chinese_count"] == 0


def test_compiler_validation_uses_real_cl(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path)
    metrics = run_redqueen_hydrabudget_compiler_validation(dataset, tmp_path / "records", supported_spot=1, boundary_spot=1, compile_worker_count=1)
    assert metrics["backend_type"] == "real_c_compiler"
    assert metrics["compiler_name"] == "cl"


def test_historical_regression_v0_9_17(tmp_path: Path) -> None:
    result = _probe(tmp_path)
    assert result["historical"]["historical_regression_gate_passed"] is True


def test_cross_process_reload_best_v0_9_17(tmp_path: Path) -> None:
    result = _probe(tmp_path)
    assert result["persistence"]["cross_process_reload_passed"] is True


def test_readiness_no_turing_claim(tmp_path: Path) -> None:
    result = _probe(tmp_path)
    assert "turing" not in result["readiness"]["recommended_claim_level"].lower()
    assert "Turing completeness" in result["mainline"]["still_not_proven"]


def test_no_expression_oracle_import() -> None:
    for path in Path("jianmu/self_learning/darwinforge").glob("*redqueen*.py"):
        assert "expression_oracle" not in path.read_text(encoding="utf-8")
    for path in Path("jianmu/self_learning/darwinforge").glob("hydrabudget*.py"):
        assert "expression_oracle" not in path.read_text(encoding="utf-8")


def test_no_external_api_calls() -> None:
    for pattern in ["*redqueen*.py", "hydrabudget*.py"]:
        for path in Path("jianmu/self_learning/darwinforge").glob(pattern):
            text = path.read_text(encoding="utf-8").lower()
            assert "requests." not in text
            assert "urllib" not in text
            assert "openai" not in text


def test_no_hardcoded_keyword_gate() -> None:
    for pattern in ["*redqueen*.py", "hydrabudget*.py"]:
        for path in Path("jianmu/self_learning/darwinforge").glob(pattern):
            assert "keyword gate" not in path.read_text(encoding="utf-8").lower()


def test_real_promotion_disabled(tmp_path: Path) -> None:
    result = _probe(tmp_path)
    assert result["integrity"]["real_promotion_enabled"] is False
    assert result["integrity"]["hydra_budget_is_shadow_only"] is True
