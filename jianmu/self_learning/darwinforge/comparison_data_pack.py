from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def generate_comparison_data_pack(records: Dict[str, Any], output_dir: str | Path) -> Dict[str, Any]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    modes = records.get("mode_results", [])
    multiseed = records.get("multiseed", {}).get("seeds", [])
    external = records.get("expanded_external_ood", {}).get("by_class", [])
    baseline = records.get("baseline", {}).get("results", [])
    ablation = records.get("ablation", {}).get("results", [])
    files = []
    files.append(_write_table(out, "scale_vs_metric", modes, ["mode", "train_sample_count", "eval_sample_count", "external_ood_sample_count", "supported_retention_rate", "external_ood_false_accept_rate", "cross_process_reload_passed", "runtime_seconds"]))
    files.append(_write_table(out, "state_size_runtime", records.get("scale_profiles", []), ["mode", "state_size_bytes", "serialization_time_seconds", "reload_time_seconds", "cross_process_eval_time_seconds", "samples_per_second"]))
    files.append(_write_table(out, "seed_stability", multiseed, ["seed", "mode", "supported_retention_rate", "external_ood_false_accept_rate", "cross_process_reload_passed", "state_hash"]))
    files.append(_write_table(out, "external_ood_expansion", external, ["class_name", "sample_count", "rejection_rate", "false_accept_rate", "quarantine_rate", "isolation_rate"]))
    files.append(_write_table(out, "baseline_harness_summary", baseline, ["method", "mode", "seed", "supported_retention_rate", "external_ood_false_accept_rate", "runtime_seconds", "limitations"]))
    files.append(_write_table(out, "ablation_summary", ablation, ["variant", "supported_retention_rate", "external_ood_false_accept_rate", "delta_vs_full", "notes"]))
    notes_path = out / "paper_update_notes.md"
    notes_path.write_text(
        "\n".join(
            [
                "# v0.9.1 Paper Update Notes",
                "",
                "- Large-scale full-state reproduction results can enter paper v2 only for completed modes.",
                "- Baseline and ablation harness results are framework evidence, not same-size LLM comparisons.",
                "- Partial or skipped modes must be labelled as partial/skipped.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    files.append(str(notes_path))
    return {"comparison_data_pack_generated": True, "comparison_data_paths": files}


def _write_table(out: Path, name: str, rows: Iterable[Dict[str, Any]], fields: List[str]) -> str:
    rows = list(rows)
    csv_path = out / f"{name}.csv"
    json_path = out / f"{name}.json"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "missing") for field in fields})
    json_path.write_text(json.dumps([{field: row.get(field, "missing") for field in fields} for row in rows], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return str(csv_path)
