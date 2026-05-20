from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, List, Optional

from jianmu.self_learning.branchchain.branch_chain import LAYER_DEFINITIONS
from jianmu.self_learning.branchchain.branch_types import BranchDecision, BranchPath
from jianmu.self_learning.darwinforge.atomic_synthesis import AtomicSynthesis
from jianmu.self_learning.darwinforge.candidate import CandidateGenome
from jianmu.self_learning.darwinforge.canonicalized_training_eval import build_training_features


def force_branch_path_from_sample(sample: Dict) -> BranchPath:
    """Path-Forcing Smoke Test（强制路径冒烟测试） helper for offline audit only."""
    target_pairs = [tuple(item) for item in sample.get("target_branch_path", [])]
    target_by_layer = {layer: selected for layer, selected in target_pairs}
    if sample.get("supported") and "support_gate" not in target_by_layer:
        target_by_layer["support_gate"] = "supported"
    decisions = []
    for layer_name, options in LAYER_DEFINITIONS:
        if layer_name not in target_by_layer:
            continue
        selected = target_by_layer[layer_name]
        if selected not in options:
            continue
        decisions.append(
            BranchDecision(
                layer_name=layer_name,
                candidates=list(options),
                selected=selected,
                confidence=100,
                neuron_id=f"forced:{layer_name}:{selected}",
                evidence={"audit_only": True, "source": "target_branch_path"},
            )
        )
    return BranchPath(
        decisions=decisions,
        route_confidence=100,
        atomic_experts=["ArithmeticExpressionExpert", "TargetIRBuilderExpert", "ConsistencyCheckExpert"] if sample.get("supported") else [],
        target_builder=target_by_layer.get("target_builder", "early_exit"),
        early_exit=not sample.get("supported"),
        unsupported_reason=sample.get("unsupported_reason"),
    )


def forced_genome_from_sample(sample: Dict) -> CandidateGenome:
    path = force_branch_path_from_sample(sample)
    decisions = {decision.layer_name: decision.selected for decision in path.decisions}
    return CandidateGenome(
        genome_id=f"forced:{sample.get('sample_id', '')}",
        branch_path=path,
        atomic_expert_plan=path.atomic_experts,
        slot_binding_policy=decisions.get("slot_binding_policy", "unsupported"),
        target_builder_policy=decisions.get("target_builder", "early_exit"),
    )


def run_path_forcing_smoke_test(samples: List[Dict]) -> Dict:
    synthesis = AtomicSynthesis()
    rows = []
    for sample in samples:
        if not sample.get("supported"):
            continue
        features = build_training_features(sample["input_text"], canonicalization_enabled=True)
        genome = forced_genome_from_sample(sample)
        phenotype = synthesis.synthesize(genome, features)
        exact = phenotype.target_ir_canonical == sample.get("target_ir_canonical")
        row = {
            "sample_id": sample.get("sample_id"),
            "input_text": sample.get("input_text"),
            "canonical_text": features.get("canonical_text"),
            "target_ir_true": sample.get("target_ir_canonical"),
            "target_ir_pred": phenotype.target_ir_canonical,
            "exact_match": exact,
            "failure_reason": phenotype.failure_reason,
            "structure_policy": sample.get("structure_policy"),
            "expression_family": sample.get("expression_family"),
            "input_mode": sample.get("input_mode"),
            "target_branch_path": sample.get("target_branch_path"),
        }
        rows.append(row)
    return {
        "path_forcing_sample_count": len(rows),
        "path_forcing_exact_match_rate": _rate(rows, "exact_match"),
        "path_forcing_literal_only_success_rate": _rate([row for row in rows if row.get("structure_policy") == "literal_value"], "exact_match"),
        "path_forcing_precedence_success_rate": _rate([row for row in rows if row.get("structure_policy") == "precedence_tree"], "exact_match"),
        "path_forcing_parentheses_success_rate": _rate([row for row in rows if row.get("structure_policy") == "parenthesized_tree"], "exact_match"),
        "path_forcing_failure_count": sum(1 for row in rows if not row["exact_match"]),
        "path_forcing_failure_by_structure_policy": dict(Counter(row.get("structure_policy") for row in rows if not row["exact_match"])),
        "path_forcing_failure_by_expression_family": dict(Counter(row.get("expression_family") for row in rows if not row["exact_match"])),
        "examples": rows[:20],
        "rows": rows,
    }


def audit_supported_sample_capability(samples: List[Dict], beam_diagnostics: Optional[List[Dict]] = None) -> Dict:
    forced = run_path_forcing_smoke_test(samples)
    forced_rows = forced["rows"]
    beam_by_sample = {row.get("sample_id"): row for row in beam_diagnostics or []}
    audit_rows = []
    for row in forced_rows:
        beam = beam_by_sample.get(row["sample_id"], {})
        if row["exact_match"] and beam and not beam.get("correct_targetir_in_beam"):
            category = "router_candidate_failure"
        elif row["exact_match"]:
            category = "synthesizable_by_forced_path"
        elif _dataset_mismatch(row):
            category = "dataset_capability_mismatch"
        else:
            category = "synthesis_capability_failure"
        audit_rows.append({**row, "capability_category": category, "beam_correct_targetir_in_beam": beam.get("correct_targetir_in_beam")})
    return {
        "supported_sample_count": len(audit_rows),
        "synthesizable_by_forced_path_rate": _category_rate(audit_rows, "synthesizable_by_forced_path") + _category_rate(audit_rows, "router_candidate_failure"),
        "router_candidate_failure_rate": _category_rate(audit_rows, "router_candidate_failure"),
        "synthesis_capability_failure_rate": _category_rate(audit_rows, "synthesis_capability_failure"),
        "dataset_capability_mismatch_count": sum(1 for row in audit_rows if row["capability_category"] == "dataset_capability_mismatch"),
        "literal_only_alignment_rate": _rate([row for row in audit_rows if row.get("structure_policy") == "literal_value"], "exact_match"),
        "precedence_alignment_rate": _rate([row for row in audit_rows if row.get("structure_policy") == "precedence_tree"], "exact_match"),
        "parenthesized_alignment_rate": _rate([row for row in audit_rows if row.get("structure_policy") == "parenthesized_tree"], "exact_match"),
        "rows": audit_rows,
    }


def _dataset_mismatch(row: Dict) -> bool:
    failure = row.get("failure_reason") or ""
    return "unsupported" in failure or "invalid_targetir" in failure


def _category_rate(rows: List[Dict], category: str) -> float:
    if not rows:
        return 0.0
    return round(sum(1 for row in rows if row["capability_category"] == category) / len(rows), 4)


def _rate(rows: List[Dict], key: str) -> float:
    if not rows:
        return 0.0
    return round(sum(1 for row in rows if row.get(key)) / len(rows), 4)
