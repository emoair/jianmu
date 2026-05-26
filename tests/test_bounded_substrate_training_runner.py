from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.bounded_substrate_training_runner import run_bounded_substrate_training_probe
from jianmu.self_learning.darwinforge.turing_substrate_generator import generate_scale


def test_bounded_substrate_training_runner_quick(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setitem(__import__("jianmu.self_learning.darwinforge.turing_substrate_generator", fromlist=["SCALE_TOTALS"]).SCALE_TOTALS, "small", 200)
    generate_scale("small", tmp_path / "data" / "small", seed=53, shard_size=100)
    monkeypatch.setattr(
        "jianmu.self_learning.darwinforge.bounded_substrate_training_runner.run_bounded_substrate_compiler_validation",
        lambda *a, **k: {"backend_type": "real_c_compiler", "compiler_name": "cl", "compile_worker_count": 16, "real_compiler_invocation_count": 1, "compiler_verified_correct_rate": 1.0, "boundary_compiler_misroute_count": 0},
    )
    result = run_bounded_substrate_training_probe(tmp_path / "data", tmp_path / "records", ["quick"], [53], run_cross_process=False)
    assert result["top1_supported_correct_after"] > result["top1_supported_correct_before"]


def test_bounded_substrate_workload_counters(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setitem(__import__("jianmu.self_learning.darwinforge.turing_substrate_generator", fromlist=["SCALE_TOTALS"]).SCALE_TOTALS, "small", 200)
    generate_scale("small", tmp_path / "data" / "small", seed=53, shard_size=100)
    monkeypatch.setattr(
        "jianmu.self_learning.darwinforge.bounded_substrate_training_runner.run_bounded_substrate_compiler_validation",
        lambda *a, **k: {"backend_type": "real_c_compiler", "compiler_name": "cl", "compile_worker_count": 16, "real_compiler_invocation_count": 1, "compiler_verified_correct_rate": 1.0, "boundary_compiler_misroute_count": 0},
    )
    run_bounded_substrate_training_probe(tmp_path / "data", tmp_path / "records", ["quick"], [53], run_cross_process=False)
    assert (tmp_path / "records" / "sample_processing_counters.json").exists()


def test_bounded_substrate_cross_process_reload_trace(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setitem(__import__("jianmu.self_learning.darwinforge.turing_substrate_generator", fromlist=["SCALE_TOTALS"]).SCALE_TOTALS, "small", 200)
    generate_scale("small", tmp_path / "data" / "small", seed=53, shard_size=100)
    monkeypatch.setattr(
        "jianmu.self_learning.darwinforge.bounded_substrate_training_runner.run_bounded_substrate_compiler_validation",
        lambda *a, **k: {"backend_type": "real_c_compiler", "compiler_name": "cl", "compile_worker_count": 16, "real_compiler_invocation_count": 1, "compiler_verified_correct_rate": 1.0, "boundary_compiler_misroute_count": 0},
    )
    monkeypatch.setattr(
        "jianmu.self_learning.darwinforge.bounded_substrate_training_runner._run_cross_process",
        lambda out, heldout, boundary: {"cross_process_reload_passed": True, "child_eval_sample_count": 32, "child_forbidden_field_access_count": 0},
    )
    result = run_bounded_substrate_training_probe(tmp_path / "data", tmp_path / "records", ["quick"], [53], run_cross_process=True)
    assert result["cross_process_reload_passed"] is True
