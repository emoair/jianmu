from dataclasses import dataclass
from typing import Dict, Optional

from jianmu.sandbox import Sandbox
from jianmu.self_learning.darwinforge.candidate import CandidateGenome, CandidatePhenotype


@dataclass
class FitnessReport:
    total_fitness: float
    target_ir_similarity: float
    target_ir_exact_match: bool
    expected_output_match: bool
    compile_success: Optional[bool]
    run_success: Optional[bool]
    unsupported_correct: bool
    invalid_targetir_penalty: float
    wrong_output_penalty: float
    path_length_penalty: float
    efficiency_bonus: float
    components: Dict

    def to_dict(self) -> Dict:
        return {
            "total_fitness": self.total_fitness,
            "target_ir_similarity": self.target_ir_similarity,
            "target_ir_exact_match": self.target_ir_exact_match,
            "expected_output_match": self.expected_output_match,
            "compile_success": self.compile_success,
            "run_success": self.run_success,
            "unsupported_correct": self.unsupported_correct,
            "invalid_targetir_penalty": self.invalid_targetir_penalty,
            "wrong_output_penalty": self.wrong_output_penalty,
            "path_length_penalty": self.path_length_penalty,
            "efficiency_bonus": self.efficiency_bonus,
            "components": dict(self.components),
        }


def compute_fitness(
    genome: CandidateGenome,
    phenotype: CandidatePhenotype,
    target: Dict,
    sandbox_optional: bool = True,
) -> FitnessReport:
    target_ir = target.get("target_ir_canonical")
    expected_output = target.get("expected_output")
    supported = bool(target.get("supported"))
    unsupported_correct = (not supported) and phenotype.unsupported_pred
    unsupported_generated = (not supported) and not phenotype.unsupported_pred
    supported_rejected = supported and phenotype.unsupported_pred
    no_confidence_reject = phenotype.unsupported_pred and genome.branch_path.reject_type == "no_confident_branch"
    correct_no_confidence_reject = (not supported) and no_confidence_reject
    wrong_no_confidence_reject = supported and no_confidence_reject
    invalid_targetir = supported and not phenotype.unsupported_pred and not phenotype.target_ir_canonical
    target_exact = supported and phenotype.target_ir_canonical == target_ir
    similarity = target_ir_similarity(phenotype.target_ir_canonical, target_ir)
    expected_match = supported and phenotype.expected_output_pred == expected_output
    compile_success = None
    run_success = None
    if sandbox_optional and phenotype.c_program:
        result = Sandbox().run(phenotype.c_program)
        compile_success = result.compile_success
        run_success = result.run_success

    invalid_penalty = -2.0 if invalid_targetir else 0.0
    wrong_output_penalty = -2.0 if supported and phenotype.expected_output_pred and not expected_match else 0.0
    path_length_penalty = -0.1 * max(len(genome.branch_path.decisions) - len(target.get("target_branch_path", [])), 0)
    efficiency_bonus = 0.2 if len(genome.branch_path.decisions) <= len(target.get("target_branch_path", [])) else 0.0

    total = 0.0
    total += 2.0 if unsupported_correct else 0.0
    total += 2.0 if correct_no_confidence_reject else 0.0
    total += 3.0 if target_exact else 0.0
    total += 2.0 if expected_match else 0.0
    total += 1.0 if compile_success else 0.0
    total += 1.0 if run_success else 0.0
    total += efficiency_bonus
    total += similarity
    total -= 4.0 if unsupported_generated else 0.0
    total -= 1.0 if supported_rejected else 0.0
    total -= 2.5 if wrong_no_confidence_reject else 0.0
    total += invalid_penalty + wrong_output_penalty + path_length_penalty

    return FitnessReport(
        total_fitness=round(total, 4),
        target_ir_similarity=similarity,
        target_ir_exact_match=bool(target_exact),
        expected_output_match=bool(expected_match),
        compile_success=compile_success,
        run_success=run_success,
        unsupported_correct=bool(unsupported_correct),
        invalid_targetir_penalty=invalid_penalty,
        wrong_output_penalty=wrong_output_penalty,
        path_length_penalty=round(path_length_penalty, 4),
        efficiency_bonus=efficiency_bonus,
        components={
            "unsupported_generated": unsupported_generated,
            "supported_rejected": supported_rejected,
            "no_confidence_reject": no_confidence_reject,
            "correct_no_confidence_reject": correct_no_confidence_reject,
            "wrong_no_confidence_reject": wrong_no_confidence_reject,
            "invalid_targetir": invalid_targetir,
            "failure_reason": phenotype.failure_reason,
        },
    )


def target_ir_similarity(predicted: Optional[str], target: Optional[str]) -> float:
    if predicted is None and target is None:
        return 1.0
    if not predicted or not target:
        return 0.0
    pred_tokens = _tokens(predicted)
    target_tokens = _tokens(target)
    if not pred_tokens or not target_tokens:
        return 0.0
    return round(len(pred_tokens & target_tokens) / len(pred_tokens | target_tokens), 4)


def _tokens(canonical: str):
    token = ""
    tokens = set()
    for ch in canonical:
        if ch.isalnum() or ch == "-":
            token += ch
        else:
            if token:
                tokens.add(token)
                token = ""
    if token:
        tokens.add(token)
    return tokens
