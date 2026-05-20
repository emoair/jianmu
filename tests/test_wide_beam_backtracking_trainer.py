import json
from pathlib import Path

from jianmu.self_learning.branchchain.toy_dataset import build_architecture_aligned_toy_dataset
from jianmu.self_learning.darwinforge.wide_beam_backtracking_trainer import (
    WideBeamBacktrackingTrainer,
    WideBeamBacktrackingTrainerConfig,
    write_wide_beam_outputs,
)


def _small_splits():
    samples = build_architecture_aligned_toy_dataset()
    supported = [sample for sample in samples if sample["supported"]]
    unsupported = [sample for sample in samples if not sample["supported"]]
    return supported[:8], supported[8:12], unsupported[:4]


def test_wide_beam_backtracking_trainer_quick_mode_runs(tmp_path):
    train, eval_samples, ood = _small_splits()
    config = WideBeamBacktrackingTrainerConfig.for_mode(
        "quick",
        generations=1,
        train_limit=6,
        eval_limit=4,
        ood_limit=2,
        population_per_layer=8,
        beam_size=8,
        proposals_per_layer=3,
        max_complete_paths=16,
    )

    metrics = WideBeamBacktrackingTrainer(train, eval_samples, ood, config).train()
    paths = write_wide_beam_outputs(metrics, tmp_path)

    assert metrics["sample_count"] == 6
    assert "target_ir_exact_match_top1" in metrics
    assert Path(paths["metrics_path"]).exists()
    assert Path(paths["report_path"]).exists()


def test_metrics_include_clone_and_backtracking_counts(tmp_path):
    train, eval_samples, ood = _small_splits()
    config = WideBeamBacktrackingTrainerConfig.for_mode(
        "quick",
        generations=3,
        backtracking_patience=1,
        train_limit=6,
        eval_limit=4,
        ood_limit=2,
        population_per_layer=8,
        beam_size=8,
        proposals_per_layer=3,
        clone_count_per_layer=2,
        max_complete_paths=16,
    )

    metrics = WideBeamBacktrackingTrainer(train, eval_samples, ood, config).train()
    write_wide_beam_outputs(metrics, tmp_path)

    assert "clone_promotion_count" in metrics
    assert "clone_discard_count" in metrics
    assert "backtracking_event_count" in metrics
    assert metrics["backtracking_event_count"] >= 1


def test_report_contains_chinese_annotations(tmp_path):
    train, eval_samples, ood = _small_splits()
    config = WideBeamBacktrackingTrainerConfig.for_mode("quick", generations=1, train_limit=4, eval_limit=2, ood_limit=1, population_per_layer=8)
    metrics = WideBeamBacktrackingTrainer(train, eval_samples, ood, config).train()
    paths = write_wide_beam_outputs(metrics, tmp_path)
    report = Path(paths["report_path"]).read_text(encoding="utf-8")

    assert "Wide-Beam Backtracking Search（宽束回溯搜索）" in report
    assert "Full Path Diagnostics（完整路径诊断）" in report
    assert "Branch Beam Size（分支束宽）" in report


def test_written_metrics_are_json(tmp_path):
    train, eval_samples, ood = _small_splits()
    config = WideBeamBacktrackingTrainerConfig.for_mode("quick", generations=1, train_limit=4, eval_limit=2, ood_limit=1, population_per_layer=8)
    metrics = WideBeamBacktrackingTrainer(train, eval_samples, ood, config).train()
    paths = write_wide_beam_outputs(metrics, tmp_path)

    payload = json.loads(Path(paths["metrics_path"]).read_text(encoding="utf-8"))

    assert payload["sample_count"] == metrics["sample_count"]
    assert "diagnostics" not in payload


def test_no_expression_oracle_import_in_wide_beam_modules():
    for path in [
        Path("jianmu/self_learning/darwinforge/beam_backtracking.py"),
        Path("jianmu/self_learning/darwinforge/layer_clone.py"),
        Path("jianmu/self_learning/darwinforge/path_diagnostics.py"),
        Path("jianmu/self_learning/darwinforge/wide_beam_backtracking_trainer.py"),
    ]:
        source = path.read_text(encoding="utf-8")
        assert "expression_oracle" not in source
        assert "parse_controlled_expression" not in source


def test_no_external_api_calls_in_wide_beam_modules():
    for path in [
        Path("jianmu/self_learning/darwinforge/beam_backtracking.py"),
        Path("jianmu/self_learning/darwinforge/layer_clone.py"),
        Path("jianmu/self_learning/darwinforge/path_diagnostics.py"),
        Path("jianmu/self_learning/darwinforge/wide_beam_backtracking_trainer.py"),
    ]:
        source = path.read_text(encoding="utf-8")
        assert "requests" not in source
        assert "httpx" not in source
        assert "openai" not in source


def test_no_flat_classifier_imports_in_wide_beam_modules():
    for path in [
        Path("jianmu/self_learning/darwinforge/beam_backtracking.py"),
        Path("jianmu/self_learning/darwinforge/layer_clone.py"),
        Path("jianmu/self_learning/darwinforge/path_diagnostics.py"),
        Path("jianmu/self_learning/darwinforge/wide_beam_backtracking_trainer.py"),
    ]:
        source = path.read_text(encoding="utf-8")
        assert "learned_router.perceptron" not in source
        assert "arithmetic_targetir.hashed_perceptron" not in source
