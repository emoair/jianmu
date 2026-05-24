from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def write_arithmetic_comparison_pack(out_dir: str | Path, stage_rows: List[Dict[str, Any]], heldout: Dict[str, Any], boundary: Dict[str, Any], compiler: Dict[str, Any], counters: Dict[str, Any], cross: Dict[str, Any], summary: Dict[str, Any]) -> Dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    paths += _write_rows(out / "arithmetic_stage_metrics", stage_rows)
    paths += _write_rows(out / "heldout_arithmetic_metrics", [{"stage": k, **v} for k, v in heldout.get("by_stage", {}).items()])
    paths += _write_rows(out / "boundary_arithmetic_metrics", boundary.get("by_category", []))
    paths += _write_rows(out / "compiler_spot_audit", [compiler])
    paths += _write_rows(out / "workload_counter_summary", [counters])
    paths += _write_rows(out / "cross_process_reload_summary", [cross])
    (out / "arithmetic_probe_summary.md").write_text("\n".join([
        "# Arithmetic Probe Summary",
        "",
        f"- recommended_claim_level: {summary.get('recommended_claim_level')}",
        f"- ready_for_arithmetic_probe_claim: {summary.get('ready_for_arithmetic_probe_claim')}",
        "- This pack is for paper v2 comparison data and does not claim solved arithmetic.",
    ]) + "\n", encoding="utf-8")
    paths.append(str(out / "arithmetic_probe_summary.md"))
    return {"comparison_data_paths": paths}


def _write_rows(base: Path, rows: List[Dict[str, Any]]) -> List[str]:
    json_path = base.with_suffix(".json")
    csv_path = base.with_suffix(".csv")
    json_path.write_text(json.dumps({"rows": rows}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    fields = sorted({key for row in rows for key in row.keys()}) if rows else ["empty"]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return [str(csv_path), str(json_path)]
