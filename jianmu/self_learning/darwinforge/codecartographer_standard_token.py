from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.codecartographer_module_schema import TOKEN_VERSION


def descriptor_to_standard_token(descriptor: Dict[str, Any]) -> Dict[str, Any]:
    module = descriptor["module_descriptor"]
    features = descriptor["feature_classification_descriptor"]
    difficulty = descriptor["difficulty_descriptor"]
    logic = descriptor["logic_structure_descriptor"]
    sequence: List[str] = [
        "MODULE_BEGIN",
        f"name={module['module_name']}",
        "MODULE_CATEGORY",
        module["module_category"],
    ]
    for key in sorted(k for k in features if k.startswith("has_") or k.endswith("_explicit")):
        sequence.extend(["FEATURE", f"{key}={str(features[key]).lower()}"])
    sequence.extend(["DIFFICULTY", f"level={difficulty['level']}", f"reason={difficulty['reason']}"])
    sequence.extend(["SUPPORT_STATUS", module["support_status"]])
    if features.get("experimental_features"):
        sequence.extend(["EXPERIMENTAL_FEATURES", ",".join(features["experimental_features"])])
    if features.get("unsupported_features"):
        sequence.extend(["UNSUPPORTED_FEATURES", ",".join(features["unsupported_features"])])
    classification_count = len(sequence)
    for fn in descriptor["function_descriptors"]:
        sequence.extend(["FUNCTION_BEGIN", f"name={fn['function_name']}", "RETURNS", fn["return_type"], "ARGS", f"count={fn['arg_count']}"])
        for var in fn["local_int_variables"]:
            sequence.extend(["LOCAL_VAR", var, "INIT_INT", "0"])
        for flow in logic["control_flow"]:
            if flow == "bounded_for":
                sequence.extend(["LOOP_FIXED", "BOUND_EXPLICIT", "UPDATE_ORDER_EXPLICIT"])
            elif flow == "bounded_while":
                sequence.extend(["WHILE_FUEL", "BOUND_EXPLICIT"])
            elif flow == "if_else":
                sequence.extend(["IF", "CONDITION_OPERATOR_EXPLICIT", "ELSE_MARKER"])
        sequence.extend(["RETURN", fn["return_target"], "FUNCTION_END"])
    sequence.append("MODULE_END")
    text = "\n".join(sequence)
    return {
        "token_version": TOKEN_VERSION,
        "token_sequence": sequence,
        "token_text": text,
        "token_hash": _hash(text),
        "classification_token_count": classification_count,
        "logic_token_count": len(sequence) - classification_count,
        "reversible_to_ir": module["support_status"] != "unsupported",
    }


def token_has_raw_target_ir(token: Dict[str, Any]) -> bool:
    text = token["token_text"]
    return text.strip().startswith("{") or '"op"' in text or '"body"' in text


def token_contains_c_source(token: Dict[str, Any]) -> bool:
    text = token["token_text"]
    return "#include" in text or "int main" in text or "{ return" in text


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
