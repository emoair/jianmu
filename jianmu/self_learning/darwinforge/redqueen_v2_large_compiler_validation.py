from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.redqueen_v2_compiler_validation import build_redqueen_v2_compiler_validation


def run_redqueen_v2_large_compiler_validation(output_records: str | Path, target: int = 5000, compile_worker_count: int = 16, fallback_worker_count: int = 8) -> Dict[str, Any]:
    del fallback_worker_count
    out = Path(output_records)
    metrics = build_redqueen_v2_compiler_validation(out, supported_spot=target, boundary_spot=target, compile_worker_count=compile_worker_count)
    _write_json(out / "redqueen_v2_large_compiler_validation.json", metrics)
    src = out / "redqueen_v2_compiler_trace_manifest.json"
    dst = out / "redqueen_v2_large_compiler_trace_manifest.json"
    if src.exists():
        shutil.copyfile(src, dst)
    return metrics


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
