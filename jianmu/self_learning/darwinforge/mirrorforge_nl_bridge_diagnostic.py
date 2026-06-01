from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def build_nl_bridge_diagnostic(output_records: str | Path) -> Dict[str, Any]:
    result = {
        "nl_bridge_diagnostic_completed": True,
        "natural_language_layer_completed": False,
        "stable_token_fields_for_nl": ["variable_initial_value", "loop_bound", "condition_operator", "output_variable", "update_order"],
        "unstable_token_fields_for_nl": ["minimal_scope_markers", "format separators", "compressed aliases"],
        "fields_too_ir_like": ["PROGRAM_BEGIN/PROGRAM_END", "VAR/INIT", "raw structural nesting delimiters"],
        "recommended_nl_annotation_schema": {
            "source_text": "Chinese problem statement",
            "mirror_token_target": "semantic/compressed MirrorToken target",
            "alignment_spans": "optional phrase-to-token slots",
            "support_status": "current_supported/future_domain/unsupported/review",
            "expected_action": "train_current/isolate_future/reject/review",
        },
        "recommended_chinese_to_token_training_format": "Chinese NL input paired with semantic MirrorToken, not raw target_ir and not expected_output.",
        "minimum_required_nl_dataset_size_estimate": 250000,
        "risks_before_nl_adapter": ["slot binding ambiguity", "loop bound paraphrase errors", "unsupported feature over-acceptance"],
        "ready_for_nl_to_mirrortoken_adapter_probe": True,
    }
    _write_json(Path(output_records) / "nl_to_mirrortoken_bridge_diagnostic.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
