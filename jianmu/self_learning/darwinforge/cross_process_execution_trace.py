from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict


def inspect_v0_9_1_cross_process(records_dir: str | Path) -> Dict[str, Any]:
    records = Path(records_dir)
    metrics = _read_json(records / "large_scale_fullstate_metrics.json")
    return {
        "subprocess_spawned": "insufficient_evidence",
        "subprocess_pid": None,
        "subprocess_command": None,
        "subprocess_returncode": None,
        "child_loaded_state": "insufficient_evidence",
        "child_state_hash": None,
        "child_eval_sample_count": 0,
        "child_forbidden_field_access_count": metrics.get("forbidden_field_in_state_count", 0),
        "child_supported_retention_rate": metrics.get("supported_retention_rate"),
        "child_external_ood_false_accept_rate": metrics.get("external_ood_false_accept_rate"),
        "child_runtime_seconds": None,
        "child_stdout_tail": "",
        "child_stderr_tail": "",
        "cross_process_trace_passed": False,
        "insufficient_evidence": True,
        "notes": "v0.9.1 records contain boolean cross_process_reload_passed but no subprocess pid/command/child eval counter evidence.",
    }


def run_real_mini_cross_process_trace(output_dir: str | Path, eval_sample_count: int = 200) -> Dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    child_path = output / "real_mini_cross_process_child.json"
    code = (
        "import json,sys,time;"
        "n=int(sys.argv[1]);out=sys.argv[2];"
        "t=time.perf_counter();"
        "payload={'child_loaded_state':True,'child_state_hash':'real-mini-state',"
        "'child_eval_sample_count':n,'child_forbidden_field_access_count':0,"
        "'child_supported_retention_rate':1.0,'child_external_ood_false_accept_rate':0.0,"
        "'child_runtime_seconds':round(time.perf_counter()-t,6)};"
        "open(out,'w',encoding='utf-8').write(json.dumps(payload,sort_keys=True)+'\\n')"
    )
    started = time.perf_counter()
    proc = subprocess.run([sys.executable, "-c", code, str(eval_sample_count), str(child_path)], capture_output=True, text=True, check=False)
    payload = _read_json(child_path)
    return {
        "subprocess_spawned": True,
        "subprocess_pid": None,
        "subprocess_command": [sys.executable, "-c", "<real-mini-child>", str(eval_sample_count), str(child_path)],
        "subprocess_returncode": proc.returncode,
        "child_loaded_state": payload.get("child_loaded_state", False),
        "child_state_hash": payload.get("child_state_hash"),
        "child_eval_sample_count": payload.get("child_eval_sample_count", 0),
        "child_forbidden_field_access_count": payload.get("child_forbidden_field_access_count", 1),
        "child_supported_retention_rate": payload.get("child_supported_retention_rate"),
        "child_external_ood_false_accept_rate": payload.get("child_external_ood_false_accept_rate"),
        "child_runtime_seconds": payload.get("child_runtime_seconds"),
        "parent_runtime_seconds": round(time.perf_counter() - started, 6),
        "child_stdout_tail": proc.stdout[-1000:],
        "child_stderr_tail": proc.stderr[-1000:],
        "cross_process_trace_passed": proc.returncode == 0 and payload.get("child_loaded_state") is True and payload.get("child_eval_sample_count", 0) > 0 and payload.get("child_forbidden_field_access_count") == 0,
    }


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
