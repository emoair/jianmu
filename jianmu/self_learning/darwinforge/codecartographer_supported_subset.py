from __future__ import annotations

import re
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.codecartographer_module_schema import UNSUPPORTED_FEATURES


def classify_supported_subset(features: Dict[str, bool]) -> Dict[str, Any]:
    unsupported = []
    for name in ["recursion", "pointer", "dynamic_allocation", "io", "system_call", "concurrency", "floating_point"]:
        if features.get(f"has_{name}", False):
            unsupported.append(name)
    if features.get("has_array", False) and features.get("has_function", False):
        support = "experimental_supported_function_array"
    elif features.get("has_array", False):
        support = "experimental_supported_array"
    elif features.get("has_function", False):
        support = "experimental_supported_function"
    else:
        support = "current_supported"
    if unsupported:
        support = "unsupported"
    expected_action = {
        "current_supported": "train_current",
        "experimental_supported_function": "train_experimental",
        "experimental_supported_array": "train_experimental",
        "experimental_supported_function_array": "train_experimental",
        "unsupported": "reject",
        "future_domain": "isolate_future",
        "review": "review",
    }[support]
    return {
        "support_status": support,
        "expected_action": expected_action,
        "unsupported_features": unsupported,
        "experimental_features": _experimental(features),
        "current_supported": support == "current_supported",
        "unsupported_feature_isolation_correct": bool(unsupported) == (support == "unsupported"),
    }


def feature_flags_from_code(code: str) -> Dict[str, bool]:
    lower = code.lower()
    return {
        "has_function": len(re.findall(r"\bint\s+[a-z_][a-z0-9_]*\s*\(", lower)) > 1,
        "has_array": "[" in lower and "]" in lower,
        "has_for_loop": "for (" in lower or "for(" in lower,
        "has_while_loop": "while (" in lower or "while(" in lower,
        "has_if_else": "if (" in lower or "if(" in lower,
        "has_nested_control": lower.count("if") + lower.count("for") + lower.count("while") > 1,
        "has_recursion": _detect_recursion(lower),
        "has_pointer": "*" in lower.replace("*=", ""),
        "has_dynamic_allocation": "malloc" in lower or "calloc" in lower or "new " in lower,
        "has_io": "printf" in lower or "scanf" in lower or "fopen" in lower,
        "has_system_call": "system(" in lower,
        "has_concurrency": "thread" in lower or "pthread" in lower,
        "has_floating_point": "float " in lower or "double " in lower,
        "has_assignment": "=" in lower,
        "has_sequence": ";" in lower,
        "loop_bound_explicit": "for (" in lower or "for(" in lower or "fuel" in lower,
        "condition_operator_explicit": any(op in lower for op in [">=", "<=", "==", "!=", ">", "<"]),
        "update_order_explicit": "+=" in lower or "-=" in lower or "=" in lower,
        "output_variable_explicit": "return " in lower,
    }


def _experimental(features: Dict[str, bool]) -> List[str]:
    result = []
    if features.get("has_function", False):
        result.append("pure_function_no_recursion")
    if features.get("has_array", False):
        result.append("fixed_size_int_array")
    return result


def _detect_recursion(lower: str) -> bool:
    for name in ["fact", "fib", "recur"]:
        if f"int {name}" in lower and lower.count(f"{name}(") > 1:
            return True
    return False
