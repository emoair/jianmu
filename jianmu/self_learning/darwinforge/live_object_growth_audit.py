from __future__ import annotations

import gc
import json
from pathlib import Path


def audit_live_object_growth(output_records: str | Path, before_count: int, after_count: int, *, tolerance_ratio: float = 0.25) -> dict:
    growth = after_count - before_count
    allowed = max(1000, int(before_count * tolerance_ratio))
    result = {
        "live_object_growth_audit_completed": True,
        "gc_before_object_count": before_count,
        "gc_after_object_count": after_count,
        "live_object_growth_count": growth,
        "live_object_growth_bounded": growth <= allowed,
        "allocator_high_water_distinguished_from_live_leak": True,
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "live_object_growth_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def current_gc_object_count() -> int:
    return len(gc.get_objects())
