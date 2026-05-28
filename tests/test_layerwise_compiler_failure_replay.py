import json

from jianmu.self_learning.darwinforge.layerwise_compiler_failure_replay import run_layerwise_failure_replay


def test_layerwise_failure_replay_does_not_skip_failures(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "compiler_validation_trace_layerwise_sparse_1B_freeze_prune.jsonl").write_text(
        json.dumps({"compiler_invoked": True, "compiler_verified_correct": False, "sample_id_hash": "missing", "exception_type": "TimeoutExpired"}) + "\n",
        encoding="utf-8",
    )
    dataset = tmp_path / "dataset" / "large"
    dataset.mkdir(parents=True)
    out = tmp_path / "out"
    metrics = run_layerwise_failure_replay(dataset.parent, src, out, worker_counts=(16,), timeout_seconds=1)
    assert metrics["original_failure_count"] == 1
    assert metrics["replay_remaining_failure_count"] == 1
    assert "not skipped" in (out / "failure_replay_trace.jsonl").read_text(encoding="utf-8")
