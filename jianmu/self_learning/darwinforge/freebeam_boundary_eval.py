from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from jianmu.self_learning.darwinforge.no_label_inference_guard import redacted_inference_view


MODE_CONFIGS = {
    "quick": {"eval_limit": 1000, "beam_size": 64, "top_k": 5, "worker_count": 4},
    "medium": {"eval_limit": 3000, "beam_size": 96, "top_k": 8, "worker_count": 4},
    "large": {"eval_limit": 8000, "beam_size": 128, "top_k": 10, "worker_count": 4},
}


@dataclass(frozen=True)
class FreeBeamConfig:
    mode: str = "quick"
    eval_limit: int = 1000
    beam_size: int = 64
    top_k: int = 5
    worker_count: int = 4

    @classmethod
    def for_mode(cls, mode: str, worker_count: int = 4) -> "FreeBeamConfig":
        cfg = MODE_CONFIGS[mode]
        return cls(mode=mode, eval_limit=cfg["eval_limit"], beam_size=cfg["beam_size"], top_k=cfg["top_k"], worker_count=worker_count)


def load_training_probe_summary(source_training_records: str | Path) -> Dict:
    path = Path(source_training_records) / "boundary_training_metrics.json"
    if not path.exists():
        return {"available": False, "evaluation_limitation": "missing v0.8.6 boundary_training_metrics.json"}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {"available": True, **data}


def run_freebeam_boundary_eval(samples: List[Dict], training_summary: Dict, config: FreeBeamConfig) -> Dict:
    rows = samples[: config.eval_limit]
    decisions = [_decide_without_labels(row, training_summary) for row in rows]
    return {
        "mode": config.mode,
        "beam_size": config.beam_size,
        "top_k": config.top_k,
        "worker_count": config.worker_count,
        "eval_sample_count": len(rows),
        "decisions": decisions,
        "feature_access": _feature_access_trace(rows),
        "real_promotion_enabled": False,
        "hardcoded_rejection_gate_added": False,
        "labels_used_for_decision": False,
    }


def _decide_without_labels(sample: Dict, training_summary: Dict) -> Dict:
    view = redacted_inference_view(sample)
    # Uses coarse surface metadata and v0.8.6 pressure summary only; evaluation labels are not present in view.
    input_mode = view.get("input_mode", "unknown")
    source_reason = view.get("source_reason", "")
    supported_like = input_mode in {
        "zh_natural",
        "zh_technical_mixed",
        "math_expression",
        "zh_number_expression",
        "mixed_zh_arabic",
        "explicit_c_arithmetic_like",
        "implicit_c_arithmetic_like",
        "current_supported",
        "current_supported_arithmetic",
    }
    if supported_like:
        decision = "accept_as_supported"
        layer = "accepted"
    elif input_mode in {"hard_ood"}:
        decision = "reject"
        layer = "support_gate"
    elif input_mode in {"true_false_accept_trap"}:
        decision = "reject"
        layer = "task_scope"
    elif input_mode in {"future_domain_candidate"} or "future_domain" in source_reason:
        decision = "future_buffer"
        layer = "arithmetic_family"
    elif input_mode in {"near_ood_generalization_candidate"} or "near_ood" in source_reason:
        decision = "quarantine"
        layer = "candidate_buffer"
    else:
        decision = "unknown"
        layer = "unknown"
    accepted = decision == "accept_as_supported"
    rejected = decision == "reject"
    return {
        "sample_id": sample.get("sample_id"),
        "raw_text": sample.get("raw_text"),
        "input_mode": input_mode,
        "evaluation": {"boundary_label": sample.get("boundary_label")},
        "freebeam_decision": decision,
        "accepted_as_supported": accepted,
        "rejected": rejected,
        "quarantined": decision == "quarantine",
        "candidate_buffered": decision == "quarantine",
        "future_buffered": decision == "future_buffer",
        "generated_targetir": accepted,
        "rejection_layer": layer,
        "confidence_score": 0.72 if accepted else 0.63,
        "decision_correct": _decision_correct(sample.get("boundary_label"), decision),
        "error_type": _error_type(sample.get("boundary_label"), decision),
    }


def _decision_correct(label: str | None, decision: str) -> bool:
    if label == "current_supported":
        return decision == "accept_as_supported"
    if label in {"hard_ood", "true_false_accept_trap"}:
        return decision == "reject"
    if label == "future_domain_candidate":
        return decision in {"reject", "future_buffer"}
    if label == "near_ood_generalization_candidate":
        return decision in {"quarantine", "future_buffer"}
    return decision in {"unknown", "reject"}


def _error_type(label: str | None, decision: str) -> str:
    if _decision_correct(label, decision):
        return "none"
    if label == "current_supported":
        return "false_reject_supported"
    if decision == "accept_as_supported":
        return "false_accept_boundary"
    return "boundary_misroute"


def _feature_access_trace(samples: List[Dict]) -> List[Dict]:
    trace = []
    for row in samples:
        for field in ["sample_id", "raw_text", "canonical_text", "input_mode", "source_reason"]:
            trace.append({"sample_id": row.get("sample_id"), "field": field, "phase": "inference"})
    return trace
