import re
from typing import List, Optional

from jianmu.ir import ProgramIR
from jianmu.routes import RouteCandidate
from jianmu.intent_router import _parse_expand_value, _parse_num, _parse_values, CHINESE_NUM, ENGLISH_NUM


def _extract_literal_value(text: str) -> int:
    m = re.search(r"(?:多加|再加)一个\s*(?:值?为?\s*)?(\d+)", text)
    if m:
        return int(m.group(1))
    m = re.search(r"\d+", text)
    return int(m.group()) if m else 1


class SpeculativeRouter:
    """
    Generates multiple RouteCandidate for a given input.
    Does NOT decide the winner — execution feedback does.
    """

    def generate_candidates(
        self,
        user_input: str,
        previous_ir: Optional[ProgramIR] = None,
    ) -> List[RouteCandidate]:
        has_prev = previous_ir is not None
        prev_count = len(previous_ir.variables) if has_prev else 0
        candidates = []

        # ── Candidate A: append_literal_to_existing_sum ──────────────────────
        # Requires previous_ir. Appends one new variable with extracted value.
        new_val = _extract_literal_value(user_input)
        target_count = prev_count + 1 if has_prev else 3
        candidates.append(RouteCandidate(
            route_id="append_literal_to_existing_sum",
            source="rule_candidate",
            intent={
                "action": "expand_sum_program",
                "target_var_count": target_count,
                "new_value": new_val,
            },
            expert_plan=["IncludeExpert", "ExpandSumExpert", "PrintfExpert",
                         "MainFunctionExpert", "ConsistencyCheckExpert"],
            prior_score=0.6 if has_prev else 0.1,
            requires_previous_ir=True,
            rationale="Append one literal to existing sum IR",
        ))

        # ── Candidate B: generate_new_sum_from_text ───────────────────────────
        # Ignores previous_ir. Generates fresh program from text.
        values = _parse_values(user_input)
        if values:
            n, vals = len(values), values
        else:
            n = _parse_num(user_input) or 2
            vals = [new_val] * n
        candidates.append(RouteCandidate(
            route_id="generate_new_sum_from_text",
            source="rule_candidate",
            intent={
                "action": "generate_sum_program",
                "var_count": n,
                "values": vals,
            },
            expert_plan=["IncludeExpert", "VariableDefinitionExpert", "SumExpressionExpert",
                         "PrintfExpert", "MainFunctionExpert", "ConsistencyCheckExpert"],
            prior_score=0.3,
            requires_previous_ir=False,
            rationale="Generate fresh sum program ignoring previous IR",
        ))

        # ── Candidate C: replace_last_operand ────────────────────────────────
        # Requires previous_ir. Replaces last variable's value with new_val.
        replace_count = prev_count if has_prev else 2
        candidates.append(RouteCandidate(
            route_id="replace_last_operand",
            source="rule_candidate",
            intent={
                "action": "replace_last_operand",
                "target_var_count": replace_count,
                "new_value": new_val,
            },
            expert_plan=["IncludeExpert", "ReplaceOperandExpert", "PrintfExpert",
                         "MainFunctionExpert", "ConsistencyCheckExpert"],
            prior_score=0.2 if has_prev else 0.05,
            requires_previous_ir=True,
            rationale="Replace last operand value in existing IR",
        ))

        return candidates
