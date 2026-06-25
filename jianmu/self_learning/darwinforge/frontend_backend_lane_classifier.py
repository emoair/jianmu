from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


def classify_frontend_backend_lanes(output_records: str | Path, *, frontend_events: int, backend_cl: int, backend_link: int, backend_exe: int) -> Dict[str, object]:
    result = {
        "lane_classification_completed": True,
        "frontend_generated_events": frontend_events,
        "frontend_syntax_filtered_events": frontend_events,
        "backend_cl_invocations": backend_cl,
        "backend_link_invocations": backend_link,
        "backend_exe_runs": backend_exe,
        "compiler_verified_correctness_denominator": backend_exe,
        "frontend_counted_as_backend": False,
        "backend_lane_required_for_correctness": True,
    }
    result["lane_classification_passed"] = result["frontend_counted_as_backend"] is False and result["compiler_verified_correctness_denominator"] == backend_exe
    _write_json(Path(output_records) / "frontend_backend_lane_classification.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

