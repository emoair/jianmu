from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.mirrorforge_compiler_validation import run_mirrorforge_compiler_validation


def run_abstraction_compiler_validation(output_records: str | Path, target: int = 5000, compile_worker_count: int = 16) -> Dict[str, Any]:
    out = Path(output_records)
    metrics = run_mirrorforge_compiler_validation(out, target=target, compile_worker_count=compile_worker_count)
    _write_json(out / "mirrorforge_abstraction_compiler_validation.json", metrics)
    manifest = out / "mirrorforge_compiler_trace_manifest.json"
    if manifest.exists():
        shutil.copyfile(manifest, out / "mirrorforge_abstraction_compiler_trace_manifest.json")
    return metrics


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
