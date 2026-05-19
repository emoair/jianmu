from typing import Dict, List


def build_branchchain_toy_dataset() -> List[Dict]:
    samples = [
        _supported("bc-toy-001", "写一个 C 程序输出 1+2", "addition", "binary_operation", "add(lit(1),lit(2))", "3\n"),
        _supported("bc-toy-002", "用 printf 输出 2*3", "multiplication", "binary_operation", "mul(lit(2),lit(3))", "6\n"),
        _supported("bc-toy-003", "输出 8/2", "exact_division", "binary_operation", "div(lit(8),lit(2))", "4\n"),
        _supported("bc-toy-004", "写一个 C 程序输出 1+2*3", "mixed_precedence", "precedence_tree", "add(lit(1),mul(lit(2),lit(3)))", "7\n"),
        _supported("bc-toy-005", "输出 (1+2)*3", "parentheses", "parenthesized_tree", "mul(add(lit(1),lit(2)),lit(3))", "9\n"),
        _supported("bc-toy-006", "printf 输出 一+二", "addition", "binary_operation", "add(lit(1),lit(2))", "3\n"),
        _supported("bc-toy-007", "写程序输出 -1+2", "addition", "binary_operation", "add(lit(-1),lit(2))", "1\n"),
        _supported("bc-toy-008", "输出 10-3", "subtraction", "binary_operation", "sub(lit(10),lit(3))", "7\n"),
        _supported("bc-toy-009", "输出 2+3+4", "addition", "reduce_chain", "add(add(lit(2),lit(3)),lit(4))", "9\n"),
        _unsupported("bc-toy-010", "输出 5/2", "unsupported_division_not_exact"),
        _unsupported("bc-toy-011", "写一首诗", "unsupported_non_programming"),
        _unsupported("bc-toy-012", "calculate 1 plus 2", "unsupported_language"),
        _unsupported("bc-toy-013", "联网下载一个文件", "unsupported_dangerous"),
        _supported("bc-toy-014", "main 里输出 4/2", "exact_division", "binary_operation", "div(lit(4),lit(2))", "2\n"),
        _supported("bc-toy-015", "打印 3*4+5", "mixed_precedence", "precedence_tree", "add(mul(lit(3),lit(4)),lit(5))", "17\n"),
        _supported("bc-toy-016", "输出 （2+3）*4", "parentheses", "parenthesized_tree", "mul(add(lit(2),lit(3)),lit(4))", "20\n"),
        _supported("bc-toy-017", "写一个 C 程序输出 6-2", "subtraction", "binary_operation", "sub(lit(6),lit(2))", "4\n"),
        _supported("bc-toy-018", "用 printf 输出 7+8", "addition", "binary_operation", "add(lit(7),lit(8))", "15\n"),
        _supported("bc-toy-019", "输出 9/3", "exact_division", "binary_operation", "div(lit(9),lit(3))", "3\n"),
        _unsupported("bc-toy-020", "请比较 1+2 和 3+4 哪个大", "comparison_future"),
    ]
    return samples


def _supported(sample_id, text, family, structure, target_ir, output):
    return {
        "sample_id": sample_id,
        "input_text": text,
        "target_branch_path": [
            ["task_scope", "programming"],
            ["language_target", "C" if "C" in text or "printf" in text or "main" in text else "unknown"],
            ["semantic_domain", "arithmetic"],
            ["support_gate", "supported"],
            ["arithmetic_family", family],
            ["structure_policy", structure],
            ["slot_binding_policy", "signed_number_order" if "-" in text or "负" in text else "chinese_number_order" if any(ch in text for ch in "一二两三四五六七八九十") else "surface_number_order"],
            ["target_builder", "canonical_arithmetic_targetir"],
        ],
        "target_ir_canonical": target_ir,
        "expected_output": output,
        "supported": True,
        "unsupported_reason": None,
    }


def _unsupported(sample_id, text, reason):
    return {
        "sample_id": sample_id,
        "input_text": text,
        "target_branch_path": [
            ["task_scope", "unsupported" if "calculate" in text else "non_programming" if "诗" in text else "programming"],
            ["support_gate", "unsupported"],
        ],
        "target_ir_canonical": None,
        "expected_output": None,
        "supported": False,
        "unsupported_reason": reason,
    }

