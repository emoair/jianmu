from __future__ import annotations

from typing import Any, Dict, List


DATASET_VERSION = "v0.9.22_codecartographer_standardtoken"
TOKEN_VERSION = "project_standard_token_v1"

CURRENT_SUPPORTED_FEATURES = [
    "int_variable_declaration",
    "int_constants",
    "assignment",
    "sequence",
    "safe_integer_arithmetic",
    "if_else",
    "bounded_for_loop",
    "bounded_while_with_fuel",
    "nested_bounded_control",
    "multi_variable_update",
    "return_int",
]

EXPERIMENTAL_FEATURES = [
    "pure_function_no_recursion",
    "bounded_call_graph",
    "fixed_size_int_array",
    "statically_safe_array_index",
    "array_loop_fixed_bound",
    "limited_function_array_combination",
]

UNSUPPORTED_FEATURES = [
    "recursion",
    "pointer",
    "dynamic_allocation",
    "io",
    "system_call",
    "concurrency",
    "floating_point",
    "undefined_behavior",
    "macro_heavy",
    "preprocessor_dependent",
    "struct_union",
    "switch_goto",
    "external_library_call",
]


def project_standard_token_schema() -> Dict[str, Any]:
    return {
        "dataset_version": DATASET_VERSION,
        "token_version": TOKEN_VERSION,
        "input_type": "project_standard_token",
        "classification_tokens": [
            "MODULE_BEGIN",
            "MODULE_CATEGORY",
            "FEATURE",
            "DIFFICULTY",
            "REQUIRED_FEATURES",
            "SUPPORT_STATUS",
            "EXPERIMENTAL_FEATURES",
            "UNSUPPORTED_FEATURES",
        ],
        "logic_tokens": [
            "FUNCTION_BEGIN",
            "RETURNS",
            "ARGS",
            "LOCAL_VAR",
            "INIT_INT",
            "ARRAY_INT",
            "LOOP_FIXED",
            "WHILE_FUEL",
            "IF",
            "CMP",
            "UPDATE",
            "RETURN",
            "FUNCTION_END",
            "MODULE_END",
        ],
        "current_supported_features": CURRENT_SUPPORTED_FEATURES,
        "experimental_features": EXPERIMENTAL_FEATURES,
        "unsupported_features": UNSUPPORTED_FEATURES,
        "non_claims": [
            "not arbitrary project parser",
            "not natural language layer",
            "not production support",
            "not raw target_ir",
            "not C source dump",
        ],
    }


def required_sample_fields() -> List[str]:
    return [
        "id",
        "dataset_version",
        "split",
        "input_type",
        "support_status",
        "expected_action",
        "source_kind",
        "module_descriptor",
        "function_descriptors",
        "feature_classification_descriptor",
        "logic_structure_descriptor",
        "project_standard_token",
        "target_ir",
        "expected_output",
        "compiler_expectation",
        "leakage_guard",
        "hashes",
        "provenance",
    ]
