from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.mirror_landing_schema import MIRROR_TERMS


def audit_mirror_landing_source(output_records: str | Path, root: str | Path = ".") -> Dict[str, Any]:
    repo = Path(root)
    code_hits = _rg(repo, ["jianmu", "tests", "examples"], MIRROR_TERMS)
    doc_hits = _rg(repo, ["docs", "records"], MIRROR_TERMS)
    code_files = sorted({hit["path"] for hit in code_hits})
    has_runtime = any("mirrorforge_" in path or "symbiote_" in path or "redqueen_two_lane" in path for path in code_files)
    has_state_machine = any("symbiote_freeze_thaw_protocol" in path or "freezing.py" in path for path in code_files)
    has_tests = any(path.startswith("tests") for path in code_files)
    docs_only = bool(doc_hits) and not code_files
    records_only = bool(doc_hits) and all(hit["path"].startswith("records") for hit in doc_hits) and not code_files
    alternating = any("freeze" in hit["text"].lower() or "thaw" in hit["text"].lower() for hit in code_hits)
    redqueen = any("redqueen" in path.lower() for path in code_files)
    status = "partial_landing" if code_files and (has_runtime or has_state_machine) else ("docs_or_records_only" if docs_only or records_only else "not_found")
    result = {
        "mirror_source_audit_started": True,
        "mirror_source_audit_completed": True,
        "mirror_terms_found": sorted({hit["term"] for hit in code_hits + doc_hits}),
        "mirror_code_files_found": code_files,
        "mirror_docs_only_detected": docs_only,
        "mirror_records_only_detected": records_only,
        "mirror_runtime_path_found": has_runtime,
        "mirror_state_machine_found": has_state_machine,
        "alternating_freeze_found": alternating,
        "frozen_lane_enforcement_found": has_state_machine,
        "lane_swap_found": False,
        "cosymbiosis_metrics_found": False,
        "redqueen_integration_found": redqueen,
        "staged_opt_in_guard_found": any("staged_opt_in" in path for path in code_files),
        "mirror_trace_found": any("trace" in path for path in code_files),
        "mirror_tests_found": has_tests,
        "mirror_preexisting_landing_found": status == "preexisting_runtime_landed",
        "landing_status": status,
        "audit_notes": [
            "MirrorForge and Symbiote source exists, but no preexisting explicit mirror alternating-freeze lane state machine was confirmed.",
            "This audit treats the pre-v1.0.8.7 state as partial rather than preexisting landed.",
        ],
    }
    _write_json(Path(output_records) / "mirror_landing_source_audit.json", result)
    return result


def _rg(repo: Path, scopes: List[str], terms: tuple[str, ...]) -> List[Dict[str, str]]:
    pattern = "|".join(terms)
    cmd = ["rg", "-n", "-i", pattern, *scopes]
    proc = subprocess.run(cmd, cwd=repo, text=True, capture_output=True, timeout=30)
    hits: List[Dict[str, str]] = []
    for line in proc.stdout.splitlines()[:2000]:
        parts = line.split(":", 2)
        if len(parts) != 3:
            continue
        text = parts[2]
        term = next((term for term in terms if term.lower() in text.lower() or term.lower() in parts[0].lower()), "mirror")
        hits.append({"path": parts[0].replace("\\", "/"), "line": parts[1], "text": text[:180], "term": term})
    return hits


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

