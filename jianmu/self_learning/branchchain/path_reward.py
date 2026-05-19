from typing import Dict, List, Optional, Tuple

from jianmu.self_learning.branchchain.branch_chain import decision_pairs
from jianmu.self_learning.branchchain.branch_types import BranchPath


def compute_path_reward(
    branch_path: BranchPath,
    target_branch_path: List[List[str]],
    predicted_target_ir: Optional[str],
    predicted_expected_output: Optional[str],
    target_ir_canonical: Optional[str],
    expected_output: Optional[str],
    supported: bool,
) -> Tuple[float, Dict]:
    predicted_pairs = decision_pairs(branch_path)
    target_pairs = [list(item) for item in target_branch_path]
    layer_matches = sum(1 for actual, target in zip(predicted_pairs, target_pairs) if actual == target)
    wrong_decisions = max(len(target_pairs), len(predicted_pairs)) - layer_matches
    branch_path_exact = predicted_pairs == target_pairs
    target_match = supported and predicted_target_ir == target_ir_canonical
    output_match = supported and predicted_expected_output == expected_output
    correct_unsupported = (not supported) and branch_path.early_exit
    supported_rejected = supported and branch_path.early_exit
    unsupported_generated = (not supported) and not branch_path.early_exit
    invalid_generation = supported and (not branch_path.early_exit) and predicted_target_ir is None
    wrong_target = supported and predicted_target_ir is not None and predicted_target_ir != target_ir_canonical

    reward = 0.0
    if target_match:
        reward += 1.0
    if output_match:
        reward += 0.5
    if correct_unsupported:
        reward += 0.4
    if supported_rejected:
        reward -= 1.0
    if unsupported_generated:
        reward -= 1.0
    if invalid_generation:
        reward -= 0.7
    if wrong_target:
        reward -= 0.5
    reward -= 0.3 * wrong_decisions

    components = {
        "branch_path_exact_match": branch_path_exact,
        "layer_matches": layer_matches,
        "wrong_branch_decisions": wrong_decisions,
        "target_ir_exact_match": bool(target_match),
        "expected_output_match": bool(output_match),
        "correct_unsupported_early_exit": bool(correct_unsupported),
        "supported_rejected": bool(supported_rejected),
        "unsupported_generated": bool(unsupported_generated),
        "invalid_generation": bool(invalid_generation),
        "wrong_target_ir": bool(wrong_target),
    }
    return round(reward, 4), components


def distribute_reward(branch_path: BranchPath, reward: float, gamma: float = 0.95):
    for index, decision in enumerate(branch_path.decisions):
        decision.reward = reward * (gamma ** index)

