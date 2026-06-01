from __future__ import annotations

from typing import Any, Dict, List


def build_module_descriptor(parsed: Dict[str, Any]) -> Dict[str, Any]:
    support = parsed["classification"]["support_status"]
    features = parsed["features"]
    module_category = _category(features, support)
    return {
        "module_descriptor": {
            "module_name": parsed["module_name"],
            "module_category": module_category,
            "function_count": len(parsed["functions"]),
            "support_status": support,
        },
        "function_descriptors": [
            {
                "function_name": fn["name"],
                "return_type": fn["return_type"],
                "arg_count": len(fn["args"]),
                "local_int_variables": fn["local_int_variables"],
                "return_target": fn["return_expressions"][0] if fn["return_expressions"] else "0",
            }
            for fn in parsed["functions"]
        ],
        "feature_classification_descriptor": {
            **features,
            "support_status": support,
            "experimental_features": parsed["classification"]["experimental_features"],
            "unsupported_features": parsed["classification"]["unsupported_features"],
        },
        "difficulty_descriptor": {
            "level": _difficulty(features),
            "reason": _difficulty_reason(features),
        },
        "logic_structure_descriptor": {
            "variables": _vars(parsed),
            "initial_values": _initial_values(parsed),
            "function_signatures": [f"{fn['return_type']} {fn['name']}({', '.join(fn['args'])})" for fn in parsed["functions"]],
            "arrays": ["fixed_int_array"] if features.get("has_array") else [],
            "control_flow": _control_flow(features),
            "update_order": ["declaration", "updates", "return"],
            "outputs": [fn["return_expressions"][0] for fn in parsed["functions"] if fn["return_expressions"]],
        },
    }


def _category(features: Dict[str, bool], support: str) -> str:
    if support == "unsupported":
        return "unsupported_features"
    if features.get("has_array") and features.get("has_function"):
        return "function_array_module"
    if features.get("has_array"):
        return "array_module"
    if features.get("has_function"):
        return "function_module"
    if features.get("has_for_loop") or features.get("has_while_loop"):
        return "bounded_control"
    return "arithmetic_core"


def _difficulty(features: Dict[str, bool]) -> int:
    return 1 + sum(int(features.get(key, False)) for key in ["has_if_else", "has_for_loop", "has_while_loop", "has_nested_control", "has_array", "has_function"])


def _difficulty_reason(features: Dict[str, bool]) -> str:
    reasons = [key for key in ["has_if_else", "has_for_loop", "has_while_loop", "has_nested_control", "has_array", "has_function"] if features.get(key)]
    return "_".join(reasons) if reasons else "simple_arithmetic"


def _vars(parsed: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    for fn in parsed["functions"]:
        out.extend(fn["local_int_variables"])
    return sorted(set(out))


def _initial_values(parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
    values = []
    for name in _vars(parsed):
        values.append({"name": name, "value": 0})
    return values


def _control_flow(features: Dict[str, bool]) -> List[str]:
    flow = ["sequence"]
    if features.get("has_if_else"):
        flow.append("if_else")
    if features.get("has_for_loop"):
        flow.append("bounded_for")
    if features.get("has_while_loop"):
        flow.append("bounded_while")
    return flow
