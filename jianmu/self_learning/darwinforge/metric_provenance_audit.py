from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List


SCAN_PATTERNS = ("*readiness.py", "*eval.py", "turing_frontier_schema.py")


def run_metric_provenance_audit(repo_root: str | Path, output_records: str | Path) -> Dict[str, Any]:
    root = Path(repo_root)
    out = Path(output_records)
    rows: List[Dict[str, Any]] = []
    for path in _scan_files(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        fixed = _fixed_literal_detected(text)
        metric_names = sorted(set(re.findall(r'"([A-Za-z0-9_]*(?:top1|candidate_miss|success_rate|runtime_seconds|readiness)[A-Za-z0-9_]*)"', text)))
        if not metric_names and ("GROUP_DELTAS" in text or fixed):
            metric_names = [path.stem]
        for name in metric_names:
            source_type = _classify(path, text, fixed)
            rows.append({
                "metric_name": name,
                "path": str(path.relative_to(root)),
                "source_type": source_type,
                "raw_trace_available": "trace" in text and "jsonl" in text,
                "fixed_literal_detected": fixed,
                "safe_claim_level": _safe_claim(source_type),
                "claim_boundary_violation_candidate": fixed and _strong_claim_context(text),
            })
    for path in sorted((root / "records").glob("*/*.json")):
        rows.append({
            "metric_name": path.stem,
            "path": str(path.relative_to(root)),
            "source_type": "summary_accounting" if "accounting" in path.name or "readiness" in path.name else "loaded_from_prior_records",
            "raw_trace_available": False,
            "fixed_literal_detected": False,
            "safe_claim_level": "evidence_record_only",
            "claim_boundary_violation_candidate": False,
        })
    result = {"metric_provenance_completed": True, "metrics": rows, "fixed_metric_scaffold_count": sum(1 for row in rows if row["fixed_literal_detected"])}
    _write_json(out / "metric_provenance_matrix.json", result)
    return result


def _scan_files(root: Path):
    base = root / "jianmu" / "self_learning" / "darwinforge"
    found = []
    for pattern in SCAN_PATTERNS:
        found.extend(base.glob(pattern))
    found.extend(base.glob("*_readiness.py"))
    found.extend(base.glob("*_eval.py"))
    return sorted(set(path for path in found if path.is_file()))


def _fixed_literal_detected(text: str) -> bool:
    return bool("GROUP_DELTAS" in text or re.search(r'"(?:top1|candidate_miss|.*success_rate)"\s*:\s*\d+\.\d+', text))


def _classify(path: Path, text: str, fixed: bool) -> str:
    if fixed:
        return "fixed_readiness_scaffold"
    if "jsonl" in text and "trace" in text:
        return "computed_from_raw_trace"
    if "read_json" in text or "json.loads" in text:
        return "loaded_from_prior_records"
    if "readiness" in path.name:
        return "summary_accounting"
    return "unknown"


def _safe_claim(source_type: str) -> str:
    if source_type == "computed_from_raw_trace":
        return "compiler_or_trace_backed_metric"
    if source_type == "fixed_readiness_scaffold":
        return "diagnostic_scaffold_only"
    if source_type == "summary_accounting":
        return "summary_accounting_only"
    return "requires_review"


def _strong_claim_context(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in ["production readiness", "turing", "release", "proven"])


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

