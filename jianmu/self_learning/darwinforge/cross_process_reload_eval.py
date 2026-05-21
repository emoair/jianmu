from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.external_ood_slice import generate_external_ood_slice
from jianmu.self_learning.darwinforge.full_state_reloader import load_full_state
from jianmu.self_learning.darwinforge.heldout_boundary_slices import build_heldout_boundary_slices
from jianmu.self_learning.darwinforge.reloaded_freebeam_eval import run_reloaded_freebeam_eval


def run_cross_process_reload_eval(state_dir: str | Path, dataset_dir: str | Path, output_dir: str | Path, mode: str = "quick", worker_count: int = 4) -> Dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "cross_process_child_metrics.json"
    cmd = [
        sys.executable,
        "-m",
        "jianmu.self_learning.darwinforge.cross_process_reload_eval",
        "--child",
        "--state-dir",
        str(state_dir),
        "--dataset-dir",
        str(dataset_dir),
        "--output-path",
        str(output_path),
        "--mode",
        mode,
        "--worker-count",
        str(worker_count),
    ]
    proc = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[3], text=True, capture_output=True, check=False)
    if proc.returncode != 0 or not output_path.exists():
        return {
            "cross_process_eval_completed": False,
            "subprocess_returncode": proc.returncode,
            "stderr": proc.stderr[-1000:],
            "stdout": proc.stdout[-1000:],
        }
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    payload["subprocess_returncode"] = proc.returncode
    payload["used_new_process"] = True
    return payload


def child_eval(state_dir: str | Path, dataset_dir: str | Path, output_path: str | Path, mode: str, worker_count: int) -> Dict[str, Any]:
    state = load_full_state(state_dir)
    scale_dir = Path(dataset_dir) / "large"
    if not scale_dir.exists():
        scale_dir = Path(dataset_dir) / "medium"
    eval_limit = {"quick": 1000, "medium": 3000, "large": 8000}[mode]
    heldout = build_heldout_boundary_slices(scale_dir, eval_limit=eval_limit)
    reloaded = run_reloaded_freebeam_eval(heldout["slices"]["heldout_mixed_boundary"], state, mode=mode, worker_count=worker_count)
    external = generate_external_ood_slice(mode)
    external_eval = run_reloaded_freebeam_eval(external["samples"], state, mode=mode, worker_count=worker_count)
    result = {
        "cross_process_eval_completed": True,
        "used_new_process": True,
        "state_loaded": state.get("state_loaded"),
        "persisted_state_support_level": state.get("persisted_state_support_level"),
        "no_label_inference_passed": reloaded["no_label_inference_passed"],
        "forbidden_field_access_count": reloaded["forbidden_field_access_count"],
        "current_supported_retention_rate": reloaded["current_supported_retention_rate"],
        "overall_ood_false_accept_rate": reloaded["overall_ood_false_accept_rate"],
        "external_ood_false_accept_rate": external_eval["overall_ood_false_accept_rate"],
        "false_accept_examples_count": reloaded["false_accept_examples_count"],
        "false_reject_supported_examples_count": reloaded["false_reject_supported_examples_count"],
        "over_rejection_detected": reloaded["over_rejection_detected"],
        "cross_process_reload_passed": (
            reloaded["no_label_inference_passed"]
            and reloaded["forbidden_field_access_count"] == 0
            and reloaded["current_supported_retention_rate"] >= 0.98
            and external_eval["overall_ood_false_accept_rate"] <= 0.10
            and not reloaded["over_rejection_detected"]
        ),
    }
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--dataset-dir", required=True)
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--mode", default="quick")
    parser.add_argument("--worker-count", type=int, default=4)
    args = parser.parse_args()
    if args.child:
        child_eval(args.state_dir, args.dataset_dir, args.output_path, args.mode, args.worker_count)


if __name__ == "__main__":
    main()
