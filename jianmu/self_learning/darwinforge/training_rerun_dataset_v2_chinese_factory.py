from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable

from jianmu.self_learning.darwinforge.training_data_mixer import build_training_data_mix_manifest
from jianmu.self_learning.darwinforge.training_rerun_ablation import write_dataset_ablation
from jianmu.self_learning.darwinforge.training_rerun_compiler_validation import run_training_rerun_compiler_validation
from jianmu.self_learning.darwinforge.training_rerun_eval import build_training_rerun_metrics
from jianmu.self_learning.darwinforge.training_rerun_historical_regression import write_training_rerun_historical_regression
from jianmu.self_learning.darwinforge.training_rerun_persistence import write_training_rerun_persistence
from jianmu.self_learning.darwinforge.training_rerun_readiness import build_training_rerun_readiness, write_training_rerun_integrity, write_training_rerun_mainline


def run_training_rerun_dataset_v2_chinese_factory(dataset_v2_dir: str | Path, chinese_factory_dir: str | Path, output_records: str | Path, profiles: Iterable[str], data_mix_profiles: Iterable[str], modes: Iterable[str], train_samples: int = 500_000, eval_samples: int = 50_000, heldout_samples: int = 50_000, boundary_samples: int = 50_000, compile_worker_count: int = 16, run_compiler_validation: bool = True) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    profile_list = list(profiles)
    mix_list = list(data_mix_profiles)
    mode_list = list(modes)
    mix = build_training_data_mix_manifest(dataset_v2_dir, chinese_factory_dir, out, train_samples, eval_samples, heldout_samples, boundary_samples)
    metrics = build_training_rerun_metrics(out, mix, profile_list, mix_list, mode_list)
    ablation = write_dataset_ablation(out, metrics)
    best = max(metrics["runs"], key=lambda row: row["top1_after"])
    compiler = run_training_rerun_compiler_validation(chinese_factory_dir, out, supported_spot=500, boundary_spot=500, compile_worker_count=compile_worker_count) if run_compiler_validation else {"compiler_validation_completed": False, "compiler_verified_correct_rate": 0.0}
    historical = write_training_rerun_historical_regression(out, best["top1_after"], best["candidate_miss_rate_after"])
    persistence = write_training_rerun_persistence(out, best["profile_name"], best["data_mix_profile"])
    integrity = write_training_rerun_integrity(out, mix["audit"])
    readiness = build_training_rerun_readiness(out, metrics, mix, ablation, compiler, historical, persistence, integrity, mode_list, profile_list, mix_list)
    mainline = write_training_rerun_mainline(out, readiness, mix, ablation, compiler, historical, persistence, integrity)
    return {"mix": mix, "metrics": metrics, "ablation": ablation, "compiler": compiler, "historical": historical, "persistence": persistence, "integrity": integrity, "readiness": readiness, "mainline": mainline}

