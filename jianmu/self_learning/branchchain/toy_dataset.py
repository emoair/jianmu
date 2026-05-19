from collections import Counter
from typing import Dict, List


SUPPORTED_GROUPS = [
    {
        "group": "add_1_2",
        "canonical": "add(lit(1),lit(2))",
        "output": "3\n",
        "family": "addition",
        "structure": "binary_operation",
        "slot": "surface_number_order",
        "texts": [
            ("写一个 C 程序输出 1+2", "zh_technical_mixed", "explicit_C"),
            ("输出 1+2", "zh_natural", "implicit_C"),
            ("计算一加二", "zh_natural", "implicit_C"),
            ("1+2", "math_expression", "math_expression_context"),
        ],
    },
    {
        "group": "mul_2_3",
        "canonical": "mul(lit(2),lit(3))",
        "output": "6\n",
        "family": "multiplication",
        "structure": "binary_operation",
        "slot": "surface_number_order",
        "texts": [
            ("用 printf 输出 2*3", "zh_technical_mixed", "explicit_C"),
            ("输出 2*3", "zh_natural", "implicit_C"),
            ("计算二乘三", "zh_natural", "implicit_C"),
            ("2*3", "math_expression", "math_expression_context"),
        ],
    },
    {
        "group": "div_8_2",
        "canonical": "div(lit(8),lit(2))",
        "output": "4\n",
        "family": "exact_division",
        "structure": "binary_operation",
        "slot": "surface_number_order",
        "texts": [
            ("写一个 C 程序输出 8/2", "zh_technical_mixed", "explicit_C"),
            ("输出 8/2", "zh_natural", "implicit_C"),
            ("计算八除以二", "zh_natural", "implicit_C"),
            ("8/2", "math_expression", "math_expression_context"),
        ],
    },
    {
        "group": "add_mul_1_2_3",
        "canonical": "add(lit(1),mul(lit(2),lit(3)))",
        "output": "7\n",
        "family": "mixed_precedence",
        "structure": "precedence_tree",
        "slot": "surface_number_order",
        "texts": [
            ("写一个 C 程序输出 1+2*3", "zh_technical_mixed", "explicit_C"),
            ("输出 1+2*3", "zh_natural", "implicit_C"),
            ("打印一加二乘三", "zh_natural", "implicit_C"),
            ("1+2*3", "math_expression", "math_expression_context"),
        ],
    },
    {
        "group": "paren_add_mul_1_2_3",
        "canonical": "mul(add(lit(1),lit(2)),lit(3))",
        "output": "9\n",
        "family": "parentheses",
        "structure": "parenthesized_tree",
        "slot": "surface_number_order",
        "texts": [
            ("写一个 C 程序输出 (1+2)*3", "zh_technical_mixed", "explicit_C"),
            ("输出（1+2）*3", "zh_natural", "implicit_C"),
            ("先算一加二，再乘三", "zh_natural", "implicit_C"),
            ("(1+2)*3", "math_expression", "math_expression_context"),
        ],
    },
    {
        "group": "sub_10_3",
        "canonical": "sub(lit(10),lit(3))",
        "output": "7\n",
        "family": "subtraction",
        "structure": "binary_operation",
        "slot": "surface_number_order",
        "texts": [
            ("写一个 C 程序输出 10-3", "zh_technical_mixed", "explicit_C"),
            ("输出 10-3", "zh_natural", "implicit_C"),
            ("计算十减三", "zh_natural", "implicit_C"),
            ("10-3", "math_expression", "math_expression_context"),
        ],
    },
    {
        "group": "reduce_add_2_3_4",
        "canonical": "add(add(lit(2),lit(3)),lit(4))",
        "output": "9\n",
        "family": "addition",
        "structure": "reduce_chain",
        "slot": "surface_number_order",
        "texts": [
            ("写一个 C 程序输出 2+3+4", "zh_technical_mixed", "explicit_C"),
            ("输出 2+3+4", "zh_natural", "implicit_C"),
            ("计算二加三加四", "zh_natural", "implicit_C"),
            ("2+3+4", "math_expression", "math_expression_context"),
        ],
    },
    {
        "group": "add_neg1_2",
        "canonical": "add(lit(-1),lit(2))",
        "output": "1\n",
        "family": "addition",
        "structure": "binary_operation",
        "slot": "signed_number_order",
        "texts": [
            ("写一个 C 程序输出 -1+2", "zh_technical_mixed", "explicit_C"),
            ("输出 -1+2", "zh_natural", "implicit_C"),
            ("计算负一加二", "zh_natural", "implicit_C"),
            ("-1+2", "math_expression", "math_expression_context"),
        ],
    },
]


OOD_SAMPLES = [
    ("calculate one plus two", "ood_english", "reject_unsupported_language", "unsupported_language"),
    ("sum of 1 and 2", "ood_english", "reject_unsupported_language", "unsupported_language"),
    ("write a C program to output 1+2", "ood_english", "reject_unsupported_language", "unsupported_language"),
    ("add two numbers and print the result", "ood_english", "reject_unsupported_language", "unsupported_language"),
    ("写一首诗", "ood_unrelated", "reject_non_programming", "unsupported_non_programming"),
    ("联网下载一个文件", "ood_unrelated", "reject_out_of_scope", "unsupported_dangerous"),
    ("请比较 1+2 和 3+4 哪个大", "ood_unrelated", "reject_out_of_scope", "comparison_future"),
    ("帮我查天气", "ood_unrelated", "reject_non_programming", "unsupported_non_programming"),
]


def build_branchchain_toy_dataset() -> List[Dict]:
    """Legacy v0.6.x toy dataset kept as an old-label comparison baseline."""
    samples = []
    for index, group in enumerate(SUPPORTED_GROUPS[:5], start=1):
        text, _, language = group["texts"][0 if index % 2 else 1]
        legacy_language = "C" if language == "explicit_C" else "unknown"
        samples.append(
            _supported_sample(
                f"bc-toy-{index:03d}",
                text,
                "legacy_toy",
                group,
                legacy_language,
                input_mode="zh_technical_mixed" if legacy_language == "C" else "zh_natural",
                include_support_gate=True,
            )
        )
    extra = [
        ("bc-toy-006", "用 printf 输出 一+二", SUPPORTED_GROUPS[0], "C"),
        ("bc-toy-007", "写程序输出 -1+2", SUPPORTED_GROUPS[7], "unknown"),
        ("bc-toy-008", "输出 10-3", SUPPORTED_GROUPS[5], "unknown"),
        ("bc-toy-009", "输出 2+3+4", SUPPORTED_GROUPS[6], "unknown"),
        ("bc-toy-014", "main 里输出 4/2", SUPPORTED_GROUPS[2], "C"),
        ("bc-toy-015", "打印 3*4+5", {
            "group": "mul_add_3_4_5",
            "canonical": "add(mul(lit(3),lit(4)),lit(5))",
            "output": "17\n",
            "family": "mixed_precedence",
            "structure": "precedence_tree",
            "slot": "surface_number_order",
        }, "unknown"),
        ("bc-toy-016", "输出（2+3）*4", {
            "group": "paren_add_mul_2_3_4",
            "canonical": "mul(add(lit(2),lit(3)),lit(4))",
            "output": "20\n",
            "family": "parentheses",
            "structure": "parenthesized_tree",
            "slot": "surface_number_order",
        }, "unknown"),
        ("bc-toy-017", "写一个 C 程序输出 6-2", {
            "group": "sub_6_2",
            "canonical": "sub(lit(6),lit(2))",
            "output": "4\n",
            "family": "subtraction",
            "structure": "binary_operation",
            "slot": "surface_number_order",
        }, "C"),
        ("bc-toy-018", "用 printf 输出 7+8", {
            "group": "add_7_8",
            "canonical": "add(lit(7),lit(8))",
            "output": "15\n",
            "family": "addition",
            "structure": "binary_operation",
            "slot": "surface_number_order",
        }, "C"),
        ("bc-toy-019", "输出 9/3", {
            "group": "div_9_3",
            "canonical": "div(lit(9),lit(3))",
            "output": "3\n",
            "family": "exact_division",
            "structure": "binary_operation",
            "slot": "surface_number_order",
        }, "unknown"),
    ]
    for sample_id, text, group, legacy_language in extra:
        samples.append(
            _supported_sample(
                sample_id,
                text,
                "legacy_toy",
                group,
                legacy_language,
                input_mode="zh_technical_mixed" if legacy_language == "C" else "zh_natural",
                include_support_gate=True,
            )
        )
    unsupported = [
        ("bc-toy-010", "输出 5/2", "unsupported_division_not_exact"),
        ("bc-toy-011", "写一首诗", "unsupported_non_programming"),
        ("bc-toy-012", "calculate 1 plus 2", "unsupported_language"),
        ("bc-toy-013", "联网下载一个文件", "unsupported_dangerous"),
        ("bc-toy-020", "请比较 1+2 和 3+4 哪个大", "comparison_future"),
    ]
    for sample_id, text, reason in unsupported:
        samples.append(_legacy_unsupported(sample_id, text, reason))
    return samples[:20]


def build_architecture_aligned_toy_dataset() -> List[Dict]:
    samples: List[Dict] = []
    counter = 1
    for group in SUPPORTED_GROUPS:
        for text, input_mode, language_target in group["texts"]:
            samples.append(
                _supported_sample(
                    f"aa-toy-{counter:03d}",
                    text,
                    group["group"],
                    group,
                    language_target,
                    input_mode=input_mode,
                    include_support_gate=False,
                )
            )
            counter += 1
    for text, input_mode, target_option, reason in OOD_SAMPLES:
        samples.append(_architecture_unsupported(f"aa-toy-{counter:03d}", text, input_mode, target_option, reason))
        counter += 1
    return samples


def dataset_summary(samples: List[Dict]) -> Dict:
    return {
        "dataset_size": len(samples),
        "input_mode_counts": dict(Counter(sample["input_mode"] for sample in samples)),
        "paraphrase_group_counts": dict(Counter(sample["paraphrase_group"] for sample in samples)),
        "supported_count": sum(1 for sample in samples if sample["supported"]),
        "ood_count": sum(1 for sample in samples if sample["input_mode"].startswith("ood_")),
        "language_target_distribution": dict(Counter(_target_for(sample, "language_target") for sample in samples)),
    }


def _supported_sample(sample_id, text, paraphrase_group, group, language_target, input_mode, include_support_gate):
    target_path = [
        ["task_scope", "programming"],
        ["language_target", language_target],
        ["semantic_domain", "arithmetic"],
    ]
    if include_support_gate:
        target_path.append(["support_gate", "supported"])
    target_path.extend(
        [
            ["arithmetic_family", group["family"]],
            ["structure_policy", group["structure"]],
            ["slot_binding_policy", group.get("slot", "surface_number_order")],
            ["target_builder", "canonical_arithmetic_targetir"],
        ]
    )
    return {
        "sample_id": sample_id,
        "input_text": text,
        "input_mode": input_mode,
        "paraphrase_group": paraphrase_group,
        "target_branch_path": target_path,
        "target_ir_canonical": group["canonical"],
        "expected_output": group["output"],
        "supported": True,
        "unsupported_reason": None,
    }


def _architecture_unsupported(sample_id, text, input_mode, target_option, reason):
    if target_option == "reject_unsupported_language":
        target_path = [["task_scope", "programming"], ["language_target", "reject_unsupported_language"]]
    else:
        target_path = [["task_scope", target_option]]
    return {
        "sample_id": sample_id,
        "input_text": text,
        "input_mode": input_mode,
        "paraphrase_group": reason,
        "target_branch_path": target_path,
        "target_ir_canonical": None,
        "expected_output": None,
        "supported": False,
        "unsupported_reason": reason,
    }


def _legacy_unsupported(sample_id, text, reason):
    return {
        "sample_id": sample_id,
        "input_text": text,
        "input_mode": "ood_english" if any("a" <= ch.lower() <= "z" for ch in text) else "ood_unrelated",
        "paraphrase_group": reason,
        "target_branch_path": [
            ["task_scope", "unsupported" if any("a" <= ch.lower() <= "z" for ch in text) else "non_programming" if "诗" in text else "programming"],
            ["support_gate", "unsupported"],
        ],
        "target_ir_canonical": None,
        "expected_output": None,
        "supported": False,
        "unsupported_reason": reason,
    }


def _target_for(sample: Dict, layer_name: str) -> str:
    for layer, value in sample["target_branch_path"]:
        if layer == layer_name:
            return value
    return "<none>"
