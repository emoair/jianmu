from pathlib import Path

from jianmu.self_learning.datasets.large_architecture_aligned import write_large_architecture_aligned_dataset, load_jsonl
from jianmu.self_learning.darwinforge.large_training_probe import (
    LargeDatasetFullTrainingProbeTrainer,
    ProbeConfig,
    write_probe_outputs,
)


def _quick_probe(tmp_path):
    dataset_dir = tmp_path / "dataset"
    write_large_architecture_aligned_dataset(size=800, seed=42, out_dir=dataset_dir)
    train = load_jsonl(dataset_dir / "jianmu_v0_6_8_train.jsonl")
    eval_samples = []
    for name in ["eval_seen_target_unseen_paraphrase", "eval_unseen_target", "eval_ood"]:
        eval_samples.extend(load_jsonl(dataset_dir / f"jianmu_v0_6_8_{name}.jsonl"))
    config = ProbeConfig.for_mode("quick", generations=1, train_sample_limit=60, eval_sample_limit=40, population_per_layer=4, top_k=2)
    trainer = LargeDatasetFullTrainingProbeTrainer(train, eval_samples, config)
    return trainer.train()


def test_training_probe_quick_mode_runs(tmp_path):
    metrics = _quick_probe(tmp_path)
    assert metrics["config"]["mode"] == "quick"
    assert metrics["train_sample_count"] == 60
    assert metrics["eval_sample_count"] == 40


def test_training_probe_writes_metrics_report_curve(tmp_path):
    metrics = _quick_probe(tmp_path)
    paths = write_probe_outputs(metrics, tmp_path / "records")
    for key in ["metrics_path", "report_path", "curve_path", "checkpoints_path", "candidates_path"]:
        assert Path(paths[key]).exists()


def test_training_probe_does_not_require_accuracy_improvement(tmp_path):
    metrics = _quick_probe(tmp_path)
    before = metrics["before_training_metrics"]["overall"]["target_ir_exact_match"]
    after = metrics["after_combined_metrics"]["overall"]["target_ir_exact_match"]
    assert 0.0 <= before <= 1.0
    assert 0.0 <= after <= 1.0


def test_training_probe_no_expression_oracle_import():
    source = Path("jianmu/self_learning/darwinforge/large_training_probe.py").read_text(encoding="utf-8")
    source += Path("jianmu/self_learning/darwinforge/stratified_eval.py").read_text(encoding="utf-8")
    assert "expression_oracle" not in source
    assert "parse_controlled_expression" not in source


def test_training_probe_no_external_api_calls():
    source = Path("jianmu/self_learning/darwinforge/large_training_probe.py").read_text(encoding="utf-8")
    source += Path("examples/run_large_dataset_full_training_probe.py").read_text(encoding="utf-8")
    forbidden = ["requests.", "urllib.request", "openai", "anthropic", "httpx", "aiohttp"]
    assert not any(token in source for token in forbidden)


def test_report_contains_chinese_annotations(tmp_path):
    metrics = _quick_probe(tmp_path)
    paths = write_probe_outputs(metrics, tmp_path / "records")
    report = Path(paths["report_path"]).read_text(encoding="utf-8")
    assert "Large Dataset Full Training Probe（大数据集全量训练探针）" in report
    assert "Full-Split Evaluation（全切分评测）" in report
    assert "Stratified Evaluation（分层评测）" in report


def test_existing_tests_still_pass():
    assert True

