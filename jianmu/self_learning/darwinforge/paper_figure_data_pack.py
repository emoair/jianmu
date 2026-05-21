from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def generate_paper_figure_data_pack(source_records: str | Path, output_dir: str | Path) -> Dict[str, Any]:
    source = Path(source_records)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    tables = {
        "scale_signal": _scale_signal(source),
        "boundary_before_after": _boundary_before_after(source),
        "ood_taxonomy": _ood_taxonomy(source),
        "persistence_progression": _persistence_progression(source),
        "external_ood_multiseed": _external_ood_multiseed(source),
        "non_claims_table": _non_claims_table(),
    }
    written = []
    for name, rows in tables.items():
        csv_path = out / f"{name}.csv"
        json_path = out / f"{name}.json"
        _write_csv(csv_path, rows)
        json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.extend([str(csv_path), str(json_path)])
    manifest = {"paper_figure_data_pack_generated": True, "tables": sorted(tables), "files": written, "source_records": str(source)}
    (out / "figure_data_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _scale_signal(source: Path) -> List[Dict[str, Any]]:
    rows = []
    summary = _read_json(source / "v0_8_1_1" / "xlarge_reproduction_summary.json")
    if summary:
        rows.append({"version": "v0.8.1.1", "mode": "xlarge_same_seed", "global_correct_targetir_in_beam_rate": summary.get("same_seed", {}).get("global_correct_targetir_in_beam_rate", summary.get("xlarge_same_seed_global_beam", "missing")), "candidate_space_failure_rate": summary.get("same_seed", {}).get("candidate_space_failure_rate", summary.get("xlarge_same_seed_candidate_failure", "missing")), "notes": "records/v0_8_1_1/xlarge_reproduction_summary.json"})
        rows.append({"version": "v0.8.1.1", "mode": "xlarge_alt_light", "global_correct_targetir_in_beam_rate": summary.get("alt_seed_light", {}).get("global_correct_targetir_in_beam_rate", summary.get("xlarge_alt_seed_light_global_beam", "missing")), "candidate_space_failure_rate": summary.get("alt_seed_light", {}).get("candidate_space_failure_rate", summary.get("xlarge_alt_seed_light_candidate_failure", "missing")), "notes": "records/v0_8_1_1/xlarge_reproduction_summary.json"})
    else:
        rows.append({"version": "v0.8.1.1", "mode": "xlarge", "global_correct_targetir_in_beam_rate": "missing", "candidate_space_failure_rate": "missing", "notes": "missing records/v0_8_1_1/xlarge_reproduction_summary.json"})
    return rows


def _boundary_before_after(source: Path) -> List[Dict[str, Any]]:
    metrics = _read_json(source / "v0_8_6" / "boundary_metrics_before_after.json") or _read_json(source / "v0_8_6" / "boundary_training_metrics.json")
    before = metrics.get("before_metrics", metrics.get("before", {}))
    after = metrics.get("after_metrics", metrics.get("after", {}))
    names = ["current_supported_retention_rate", "overall_ood_false_accept_rate", "true_false_accept_trap_rejection_rate", "hard_ood_rejection_rate"]
    return [{"version": "v0.8.6", "metric": name, "before": before.get(name, "missing"), "after": after.get(name, "missing"), "notes": "records/v0_8_6"} for name in names]


def _ood_taxonomy(source: Path) -> List[Dict[str, Any]]:
    candidates = [
        source / "v0_8_4" / "ood_boundary_classification.json",
        source / "v0_8_3" / "ood_precision_recheck.json",
        source / "v0_8_2" / "ood_precision_audit.json",
    ]
    for path in candidates:
        payload = _read_json(path)
        dist = payload.get("ood_boundary_distribution") or payload.get("ood_precision_distribution") or payload.get("distribution")
        if isinstance(dist, dict):
            return [{"class": key, "count": value, "source_version": path.parent.name} for key, value in sorted(dist.items())]
    return [{"class": "missing", "count": "missing", "source_version": "missing"}]


def _persistence_progression(source: Path) -> List[Dict[str, Any]]:
    versions = [("v0.8.8", source / "v0_8_8" / "persisted_router_metrics.json"), ("v0.8.9", source / "v0_8_9" / "full_state_metrics.json"), ("v0.9.0", source / "v0_9_0" / "runtime_state_capture_metrics.json")]
    rows = []
    for version, path in versions:
        payload = _read_json(path)
        ready = payload.get("arxiv_readiness_v3", payload.get("arxiv_readiness_v2", payload.get("arxiv_readiness", {})))
        rows.append(
            {
                "version": version,
                "support_level": payload.get("persisted_state_support_level", "missing"),
                "state_saved": payload.get("state_saved", "missing"),
                "state_loaded": payload.get("state_loaded", "missing"),
                "cross_process_reload_passed": payload.get("cross_process_reload", {}).get("cross_process_reload_passed", payload.get("cross_process_reload_passed", "missing")),
                "ready_for_arxiv": ready.get("ready_for_arxiv_technical_report", "missing") if isinstance(ready, dict) else "missing",
                "blocking_issue_count": len(ready.get("blocking_issues", [])) if isinstance(ready, dict) else "missing",
            }
        )
    return rows


def _external_ood_multiseed(source: Path) -> List[Dict[str, Any]]:
    rows = []
    for version, path in [("v0.8.8", source / "v0_8_8" / "multiseed_boundary_eval.json"), ("v0.8.9", source / "v0_8_9" / "multiseed_full_state_eval.json"), ("v0.9.0", source / "v0_9_0" / "multiseed_runtime_state_eval.json")]:
        payload = _read_json(path)
        seed_rows = payload.get("seed_metrics", payload.get("seeds", []))
        if isinstance(seed_rows, dict):
            seed_rows = list(seed_rows.values())
        if not seed_rows:
            rows.append({"version": version, "seed": "missing", "supported_retention": "missing", "external_ood_false_accept": "missing", "hard_ood_rejection": "missing", "trap_rejection": "missing", "future_isolation": "missing", "near_ood_quarantine": "missing"})
        for seed in seed_rows:
            rows.append({"version": version, "seed": seed.get("seed", "missing"), "supported_retention": seed.get("current_supported_retention_rate", "missing"), "external_ood_false_accept": seed.get("external_ood_false_accept_rate", seed.get("overall_ood_false_accept_rate", "missing")), "hard_ood_rejection": seed.get("hard_ood_rejection_rate", "missing"), "trap_rejection": seed.get("trap_rejection_rate", seed.get("true_false_accept_trap_rejection_rate", "missing")), "future_isolation": seed.get("future_domain_isolation_rate", "missing"), "near_ood_quarantine": seed.get("near_ood_quarantine_rate", "missing")})
    return rows


def _non_claims_table() -> List[Dict[str, str]]:
    claims = ["stable convergence", "solved OOD", "solved arithmetic", "general program synthesis", "same-size LLM advantage", "safe real promotion"]
    return [{"claim": claim, "status": "not_claimed", "reason": "outside current bounded controlled evidence"} for claim in claims]


def _write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else ["status"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
