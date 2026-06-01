from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def build_symbiote_reward_model(output_records: str | Path) -> Dict[str, Any]:
    result = {
        "reward_model_completed": True,
        "trunk_answer_correctness_is_not_sole_reward": True,
        "compiler_truth_anchor_enabled": True,
        "structural_truth_anchor_enabled": True,
        "heldout_generalization_anchor_enabled": True,
        "mirror_reward_terms": {
            "module_parse_correctness": 1.5,
            "feature_classification_correctness": 1.5,
            "standard_token_generation_correctness": 1.2,
            "token_to_ir_success": 1.0,
            "compiler_verified_correctness": 1.0,
            "redqueen_required_feature_satisfaction": 0.8,
            "heldout_module_generalization": 0.8,
            "comfort_zone_collapse_penalty": -1.5,
            "duplicate_template_penalty": -1.2,
            "structural_truth_mismatch_penalty": -1.5,
            "unsupported_feature_misroute_penalty": -2.0,
        },
        "trunk_reward_terms": {
            "top1_gain": 1.5,
            "candidate_miss_reduction": 1.5,
            "correct_output_in_beam_gain": 1.0,
            "compiler_verified_correctness": 1.0,
            "function_array_frontier_gain": 0.8,
            "heldout_module_generalization": 0.8,
            "boundary_misroute_penalty": -1.5,
            "future_domain_pollution_penalty": -1.5,
            "capability_balance_penalty": -1.0,
            "comfort_zone_overfit_penalty": -1.5,
        },
    }
    out = Path(output_records)
    _write_json(out / "symbiote_reward_model.json", result)
    (out / "symbiote_reward_trace.jsonl").write_text(json.dumps({"event": "reward_model_defined", "trunk_not_sole_verifier": True}) + "\n", encoding="utf-8")
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
