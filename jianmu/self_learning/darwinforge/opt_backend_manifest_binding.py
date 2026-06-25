from __future__ import annotations

import json
from pathlib import Path


def bind_opt_display_to_backend_manifest(output_records: str | Path, manifest_name: str = "backend_invocation_manifest.jsonl", trace_name: str = "opt_progress_trace.jsonl") -> dict:
    out = Path(output_records)
    manifest = out / manifest_name
    trace = out / trace_name
    manifest_rows = _count_lines(manifest)
    trace_rows = _count_lines(trace)
    result = {
        "opt_backend_manifest_binding_completed": True,
        "backend_manifest_path": str(manifest),
        "opt_trace_path": str(trace),
        "backend_manifest_exists": manifest.exists(),
        "opt_trace_exists": trace.exists(),
        "backend_manifest_rows": manifest_rows,
        "opt_trace_rows": trace_rows,
        "opt_display_bound_to_backend_manifest": manifest.exists() and trace.exists() and trace_rows > 0,
    }
    (out / "opt_backend_manifest_binding.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return sum(1 for line in handle if line.strip())
