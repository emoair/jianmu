from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.external_ood_slice import generate_external_ood_slice
from jianmu.self_learning.darwinforge.heldout_boundary_slices import build_heldout_boundary_slices
from jianmu.self_learning.darwinforge.reloaded_freebeam_eval import run_reloaded_freebeam_eval
from jianmu.self_learning.darwinforge.runtime_full_state_builder import load_runtime_full_state


def run_runtime_full_state_replay(
    state_dir: str | Path,
    dataset_dir: str | Path,
    output_dir: str | Path,
    mode: str = "quick",
    worker_count: int = 4,
    run_cross_process: bool = True,
    run_external_ood: bool = True,
) -> Dict[str, Any]:
    state = load_runtime_full_state(state_dir)
    samples = _heldout_samples(dataset_dir, mode)
    same = run_reloaded_freebeam_eval(samples, _persisted_state_for_eval(state), mode=mode, worker_count=worker_count)
    same["same_process_reload_passed"] = _eval_passed(same)
    external = generate_external_ood_slice(mode, output_dir) if run_external_ood else {"samples": [], "manifest": {}}
    external_eval = run_reloaded_freebeam_eval(external["samples"], _persisted_state_for_eval(state), mode=mode, worker_count=worker_count) if external["samples"] else {}
    cross = run_cross_process_runtime_reload_eval(state_dir, dataset_dir, output_dir, mode=mode, worker_count=worker_count) if run_cross_process else {"cross_process_reload_passed": False, "skip_reason": "disabled"}
    return {
        "state_loaded": state["state_loaded"],
        "persisted_state_support_level": state["persisted_state_support_level"],
        "same_process_reload": _compact(same),
        "same_process_reload_passed": same["same_process_reload_passed"],
        "cross_process_reload": cross,
        "external_ood_metrics": _compact(external_eval),
    }


def run_cross_process_runtime_reload_eval(state_dir: str | Path, dataset_dir: str | Path, output_dir: str | Path, mode: str = "quick", worker_count: int = 4) -> Dict[str, Any]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    result_path = out / "cross_process_runtime_reload_child.json"
    cmd = [
        sys.executable,
        "-m",
        "jianmu.self_learning.darwinforge.runtime_full_state_replay",
        "--child",
        "--state-dir",
        str(state_dir),
        "--dataset-dir",
        str(dataset_dir),
        "--output-path",
        str(result_path),
        "--mode",
        mode,
        "--worker-count",
        str(worker_count),
    ]
    completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        return {
            "cross_process_eval_completed": False,
            "cross_process_reload_passed": False,
            "returncode": completed.returncode,
            "stderr": completed.stderr[-2000:],
        }
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    payload["cross_process_eval_completed"] = True
    payload["cross_process_reload_passed"] = _eval_passed(payload)
    payload["used_new_process"] = True
    return payload


def _heldout_samples(dataset_dir: str | Path, mode: str) -> List[Dict[str, Any]]:
    eval_limit = {"quick": 1000, "medium": 3000, "large": 8000}.get(mode, 1000)
    scale_dir = Path(dataset_dir) / "large"
    if not scale_dir.exists():
        scale_dir = Path(dataset_dir) / "medium"
    heldout = build_heldout_boundary_slices(scale_dir, eval_limit=eval_limit, seed=42)
    return heldout["slices"]["heldout_mixed_boundary"]


def _persisted_state_for_eval(loaded_state: Dict[str, Any]) -> Dict[str, Any]:
    manifest = loaded_state.get("manifest", {})
    files = loaded_state.get("state_files", {})
    training_summary = {
        "available": True,
        "reloaded_from_runtime_full_state": True,
        "branch_population_hash": files.get("trained_branch_population.json", {}).get("state_hash"),
        "root_colony_hash": files.get("trained_root_colonies.json", {}).get("state_hash"),
    }
    return {
        "persisted_state_support_level": manifest.get("persisted_state_support_level", loaded_state.get("persisted_state_support_level", "unavailable")),
        "state_files": {"training_summary.json": {"summary": training_summary}},
    }


def _eval_passed(result: Dict[str, Any]) -> bool:
    return bool(
        result.get("no_label_inference_passed")
        and result.get("forbidden_field_access_count", 1) == 0
        and result.get("current_supported_retention_rate", 0.0) >= 0.98
        and result.get("overall_ood_false_accept_rate", 1.0) <= 0.05
        and result.get("over_rejection_detected") is False
    )


def _compact(result: Dict[str, Any]) -> Dict[str, Any]:
    compact = dict(result)
    compact.pop("decisions", None)
    compact.pop("guard", None)
    compact.pop("diagnostics", None)
    return compact


def _child_main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--dataset-dir", required=True)
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--mode", default="quick")
    parser.add_argument("--worker-count", type=int, default=4)
    args = parser.parse_args()
    loaded = load_runtime_full_state(args.state_dir)
    samples = _heldout_samples(args.dataset_dir, args.mode)
    result = run_reloaded_freebeam_eval(samples, _persisted_state_for_eval(loaded), mode=args.mode, worker_count=args.worker_count)
    compact = _compact(result)
    Path(args.output_path).write_text(json.dumps(compact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    _child_main()
