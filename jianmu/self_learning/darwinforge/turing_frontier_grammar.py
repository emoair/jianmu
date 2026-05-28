from __future__ import annotations

from typing import Any, Dict


SUPPORTED_STAGES = [
    "variable_declaration",
    "assignment_sequence",
    "multi_variable_sequence",
    "if_else_basic",
    "if_else_nested",
    "bounded_for_loop",
    "bounded_while_with_fuel",
    "nested_bounded_control",
    "bounded_control_hard_supported",
]

FRONTIER_STAGES = [
    *SUPPORTED_STAGES,
    "future_function",
    "future_array",
    "future_recursion",
    "unsupported_unbounded_loop",
    "near_ood_program",
    "true_false_accept_trap",
    "hard_ood",
    "label_review_candidate",
]


def simple_supported_ir(value: int, stage: str = "variable_declaration") -> Dict[str, Any]:
    if stage == "bounded_for_loop":
        return {
            "op": "Program",
            "body": [
                {"op": "VarDecl", "name": "result", "value": {"op": "Int", "value": 0}},
                {"op": "ForBounded", "var": "i", "bound": value, "body": [{"op": "Assign", "name": "result", "value": {"op": "Add", "args": [{"op": "Var", "name": "result"}, {"op": "Int", "value": 1}]}}]},
                {"op": "Print", "value": {"op": "Var", "name": "result"}},
            ],
        }
    if stage == "if_else_basic":
        return {
            "op": "Program",
            "body": [
                {"op": "VarDecl", "name": "x", "value": {"op": "Int", "value": value}},
                {"op": "IfElse", "cond": {"op": "Compare", "cmp": ">=", "left": {"op": "Var", "name": "x"}, "right": {"op": "Int", "value": 0}}, "then": [{"op": "Assign", "name": "x", "value": {"op": "Add", "args": [{"op": "Var", "name": "x"}, {"op": "Int", "value": 1}]}}], "else": [{"op": "Assign", "name": "x", "value": {"op": "Int", "value": 0}}]},
                {"op": "Print", "value": {"op": "Var", "name": "x"}},
            ],
        }
    return {
        "op": "Program",
        "body": [
            {"op": "VarDecl", "name": "x", "value": {"op": "Int", "value": value}},
            {"op": "Assign", "name": "x", "value": {"op": "Add", "args": [{"op": "Var", "name": "x"}, {"op": "Int", "value": 1}]}},
            {"op": "Print", "value": {"op": "Var", "name": "x"}},
        ],
    }


def expected_output_for_supported(value: int, stage: str) -> str:
    if stage == "bounded_for_loop":
        return str(value)
    return str(value + 1)


def language_features_for(category: str, stage: str) -> Dict[str, bool]:
    return {
        "has_variable_decl": category in {"current_supported_bounded_substrate", "bounded_control_hard_supported"},
        "has_assignment": category in {"current_supported_bounded_substrate", "bounded_control_hard_supported"},
        "has_sequence": category in {"current_supported_bounded_substrate", "bounded_control_hard_supported"},
        "has_if_else": "if_else" in stage or stage == "bounded_control_hard_supported",
        "has_for_loop": "for_loop" in stage or stage == "bounded_control_hard_supported",
        "has_while_loop": "while" in stage or stage == "bounded_control_hard_supported" or category == "unsupported_unbounded_loop",
        "has_nested_control": "nested" in stage or stage == "bounded_control_hard_supported",
        "has_function": category == "future_function_candidate",
        "has_array": category == "future_array_candidate",
        "has_pointer": category in {"near_ood_program", "true_false_accept_trap"},
        "has_recursion": category == "future_recursion_candidate",
        "has_unbounded_loop": category == "unsupported_unbounded_loop",
        "has_io": category == "true_false_accept_trap",
        "has_system_call": category == "true_false_accept_trap",
    }


def complexity_for(category: str, stage: str, value: int) -> Dict[str, Any]:
    loop = int("loop" in stage or category == "unsupported_unbounded_loop" or stage == "bounded_control_hard_supported")
    return {
        "statement_count": 4 + loop,
        "expression_count": 3 + loop,
        "max_ast_depth": 3 + int("nested" in stage),
        "loop_count": loop,
        "max_loop_bound": value if loop and category != "unsupported_unbounded_loop" else None,
        "estimated_step_bound": value + 4 if category in {"current_supported_bounded_substrate", "bounded_control_hard_supported"} else None,
        "function_count": 1 if category == "future_function_candidate" else 0,
        "array_access_count": 1 if category == "future_array_candidate" else 0,
        "recursion_depth_bound": 8 if category == "future_recursion_candidate" else None,
    }
