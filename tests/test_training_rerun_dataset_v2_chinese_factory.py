from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.chinese_dataset_factory import generate_codex_grammar_chinese_dataset, make_sample
from jianmu.self_learning.darwinforge.chinese_training_domain_guard import can_enter_train_current, classify_training_domain
from jianmu.self_learning.darwinforge.training_data_mixer import build_training_data_mix_manifest
from jianmu.self_learning.darwinforge.training_rerun_ablation import write_dataset_ablation
from jianmu.self_learning.darwinforge.training_rerun_compiler_validation import run_training_rerun_compiler_validation
from jianmu.self_learning.darwinforge.training_rerun_dataset_v2_chinese_factory import run_training_rerun_dataset_v2_chinese_factory
from jianmu.self_learning.darwinforge.training_rerun_eval import build_training_rerun_metrics
from jianmu.self_learning.darwinforge.training_rerun_historical_regression import write_training_rerun_historical_regression
from jianmu.self_learning.darwinforge.training_rerun_persistence import write_training_rerun_persistence
from jianmu.self_learning.darwinforge.training_rerun_readiness import build_training_rerun_readiness, write_training_rerun_integrity
from jianmu.self_learning.darwinforge.turing_frontier_v2_generator import generate_turing_frontier_v2_dataset


PROFILES = ["current_1B_reference", "combined_hot_rebalanced_balanced_sampling_1B", "layerwise_sparse_1B_freeze_prune"]
MIXES = ["dataset_v2_only", "chinese_factory_only", "dataset_v2_plus_chinese_factory_balanced", "dataset_v2_plus_chinese_factory_control_heavy", "dataset_v2_plus_chinese_factory_stage_balanced"]


def _datasets(tmp_path: Path) -> tuple[Path, Path]:
    v2 = tmp_path / "v2"
    zh = tmp_path / "zh"
    generate_turing_frontier_v2_dataset(v2, tmp_path / "r1", ["pilot"], seed=96)
    generate_codex_grammar_chinese_dataset(zh, tmp_path / "r2", ["pilot"], seed=98)
    return v2, zh


def test_training_data_mixer_blocks_non_chinese_train(tmp_path: Path) -> None:
    v2, zh = _datasets(tmp_path)
    bundle = build_training_data_mix_manifest(v2, zh, tmp_path / "out", train_limit=100)
    assert bundle["audit"]["train_current_non_chinese_count"] == 0
    assert bundle["manifest"]["dataset_sources"]["dataset_v2_train_current_allowed"] == 0


def test_training_data_mixer_blocks_future_train(tmp_path: Path) -> None:
    v2, zh = _datasets(tmp_path)
    bundle = build_training_data_mix_manifest(v2, zh, tmp_path / "out", train_limit=100)
    assert bundle["audit"]["future_domain_in_train_count"] == 0
    assert bundle["audit"]["unsupported_in_train_count"] == 0


def test_training_data_mixer_group_leakage(tmp_path: Path) -> None:
    v2, zh = _datasets(tmp_path)
    bundle = build_training_data_mix_manifest(v2, zh, tmp_path / "out", train_limit=100)
    assert bundle["audit"]["group_leakage_count"] == 0
    assert bundle["audit"]["duplicate_rate"] == 0.0


def test_chinese_training_domain_guard() -> None:
    row = make_sample(1, "pilot", "current_supported_bounded_substrate_zh")
    assert can_enter_train_current(row)
    english = make_sample(2, "pilot", "english_unrelated_request")
    assert not can_enter_train_current(english)
    assert classify_training_domain(english) == "boundary_or_review"


def test_training_rerun_ablation_outputs_best_mix(tmp_path: Path) -> None:
    v2, zh = _datasets(tmp_path)
    mix = build_training_data_mix_manifest(v2, zh, tmp_path / "out", train_limit=100)
    metrics = build_training_rerun_metrics(tmp_path / "out", mix, PROFILES, MIXES, ["quick"])
    ablation = write_dataset_ablation(tmp_path / "out", metrics)
    assert ablation["best_data_mix_profile"] == "dataset_v2_plus_chinese_factory_stage_balanced"


def test_training_rerun_eval_metrics(tmp_path: Path) -> None:
    v2, zh = _datasets(tmp_path)
    mix = build_training_data_mix_manifest(v2, zh, tmp_path / "out", train_limit=100)
    metrics = build_training_rerun_metrics(tmp_path / "out", mix, PROFILES, MIXES, ["quick"])
    best = max(metrics["runs"], key=lambda row: row["top1_after"])
    assert best["top1_after"] > 0.8274
    assert best["candidate_miss_rate_after"] < 0.1048


def test_training_rerun_compiler_validation_uses_real_cl(tmp_path: Path) -> None:
    _, zh = _datasets(tmp_path)
    metrics = run_training_rerun_compiler_validation(zh, tmp_path / "out", supported_spot=1, boundary_spot=1, compile_worker_count=1)
    assert metrics["backend_type"] == "real_c_compiler"
    assert metrics["compiler_name"] == "cl"


def test_training_rerun_boundary_blocks_future_accept(tmp_path: Path) -> None:
    result = run_training_rerun_dataset_v2_chinese_factory(*_datasets(tmp_path), tmp_path / "out", PROFILES, MIXES, ["quick"], train_samples=100, eval_samples=20, heldout_samples=20, boundary_samples=20, compile_worker_count=1, run_compiler_validation=False)
    best = max(result["metrics"]["runs"], key=lambda row: row["top1_after"])
    assert best["future_domain_supported_accept_rate"] == 0.0
    assert best["english_supported_accept_rate"] == 0.0


def test_training_rerun_historical_regression(tmp_path: Path) -> None:
    hist = write_training_rerun_historical_regression(tmp_path, 0.8584, 0.07814)
    assert hist["historical_regression_gate_passed"]
    assert hist["improved_vs_v0_9_14"]


def test_training_rerun_persistence_cross_process(tmp_path: Path) -> None:
    trace = write_training_rerun_persistence(tmp_path, "layerwise_sparse_1B_freeze_prune", "dataset_v2_plus_chinese_factory_stage_balanced")
    assert trace["cross_process_reload_passed"]
    assert trace["child_forbidden_field_access_count"] == 0


def test_training_rerun_readiness_no_turing_claim(tmp_path: Path) -> None:
    v2, zh = _datasets(tmp_path)
    result = run_training_rerun_dataset_v2_chinese_factory(v2, zh, tmp_path / "out", PROFILES, MIXES, ["quick"], train_samples=100, eval_samples=20, heldout_samples=20, boundary_samples=20, compile_worker_count=1, run_compiler_validation=False)
    assert "turing" not in result["readiness"]["recommended_claim_level"].lower()
    assert "Turing completeness" in result["mainline"]["still_not_proven"]


def test_no_expression_oracle_import() -> None:
    for path in Path("jianmu/self_learning/darwinforge").glob("training_rerun*.py"):
        assert "expression_oracle" not in path.read_text(encoding="utf-8")


def test_no_external_api_calls() -> None:
    for path in Path("jianmu/self_learning/darwinforge").glob("training_rerun*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert "requests." not in text
        assert "urllib" not in text
        assert "openai" not in text


def test_no_hardcoded_keyword_gate() -> None:
    for path in Path("jianmu/self_learning/darwinforge").glob("training_rerun*.py"):
        assert "keyword gate" not in path.read_text(encoding="utf-8").lower()


def test_real_promotion_disabled(tmp_path: Path) -> None:
    integrity = write_training_rerun_integrity(tmp_path, {"train_current_non_chinese_count": 0, "future_domain_in_train_count": 0})
    assert integrity["real_promotion_enabled"] is False
    assert integrity["profile_is_default_runtime"] is False
