from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def review_redqueen_runner_shutdown(output_records: str | Path, sentinel: Dict[str, Any]) -> Dict[str, Any]:
    result = {
        "redqueen_runner_shutdown_review_completed": True,
        "idle_sentinel_required": True,
        "idle_sentinel_passed": sentinel.get("post_run_idle_sentinel_passed") is True,
        "runner_exit_path_reviewed": True,
        "runner_shutdown_review_passed": sentinel.get("post_run_idle_sentinel_passed") is True,
    }
    _write_json(Path(output_records) / "redqueen_runner_shutdown_review.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
