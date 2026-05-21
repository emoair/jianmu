from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List


FORBIDDEN_INFERENCE_FIELDS = {
    "boundary_label",
    "expected_action",
    "nutrient_policy",
    "toxicity_policy",
    "target_ir",
    "expected_output",
    "target_branch_path",
    "current_support_status",
    "future_support_status",
}


def assert_no_label_fields_used(recorded_feature_access: Iterable[Dict], access_trace_path: str | None = None) -> Dict:
    violations: List[Dict] = []
    forbidden_seen = set()
    for row in recorded_feature_access:
        field = row.get("field")
        if field in FORBIDDEN_INFERENCE_FIELDS:
            forbidden_seen.add(field)
            violations.append(
                {
                    "sample_id": row.get("sample_id"),
                    "field": field,
                    "phase": row.get("phase", "inference"),
                    "reason": "forbidden free-beam inference field",
                }
            )
    report = {
        "no_label_inference_passed": not violations,
        "forbidden_field_access_count": len(violations),
        "forbidden_fields_seen": sorted(forbidden_seen),
        "access_trace_path": access_trace_path,
        "violation_examples": violations[:20],
    }
    if access_trace_path:
        path = Path(access_trace_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
    return report


def redacted_inference_view(sample: Dict) -> Dict:
    return {key: value for key, value in sample.items() if key not in FORBIDDEN_INFERENCE_FIELDS}
