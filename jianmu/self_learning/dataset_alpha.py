import json
import random
import hashlib
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


SEED = 20260518
DATASET_VERSION = "v0.5.6-alpha"
TOTAL_SAMPLES = 1000
TRAIN_COUNT = 800
EVAL_COUNT = 200

FAMILY_COUNTS = {
    "generate_sum_program": 250,
    "append_literal_to_existing_sum": 180,
    "append_multiple_literals_to_existing_sum": 120,
    "replace_operand": 120,
    "no_op_keep_existing": 100,
    "explicit_expression_rewrite": 100,
    "unsupported_input": 80,
    "comparison_prealpha": 50,
}

TRAIN_COUNTS = {
    "generate_sum_program": 200,
    "append_literal_to_existing_sum": 144,
    "append_multiple_literals_to_existing_sum": 96,
    "replace_operand": 96,
    "no_op_keep_existing": 80,
    "explicit_expression_rewrite": 80,
    "unsupported_input": 64,
    "comparison_prealpha": 40,
}

EVAL_COUNTS = {
    family: FAMILY_COUNTS[family] - TRAIN_COUNTS[family]
    for family in FAMILY_COUNTS
}

OUTPUT_DIR = Path("datasets") / "v0_5_6"
ALL_PATH = OUTPUT_DIR / "jianmu_zh_intent_1000.jsonl"
TRAIN_PATH = OUTPUT_DIR / "jianmu_zh_intent_1000_train.jsonl"
EVAL_PATH = OUTPUT_DIR / "jianmu_zh_intent_1000_eval.jsonl"
REPORT_PATH = OUTPUT_DIR / "jianmu_zh_intent_1000_report.md"

CHINESE_NUMBERS = {
    -3: "负三",
    -2: "-2",
    -1: "-1",
    0: "零",
    1: "一",
    2: "二",
    3: "三",
    4: "四",
    5: "五",
    6: "六",
    7: "七",
    8: "八",
    9: "九",
    10: "十",
}


def build_dataset(seed: int = SEED) -> List[Dict]:
    rng = random.Random(seed)
    samples: List[Dict] = []
    used_inputs = set()
    counters = {family: 0 for family in FAMILY_COUNTS}

    for split, split_counts in (("train", TRAIN_COUNTS), ("eval", EVAL_COUNTS)):
        for family, count in split_counts.items():
            for local_index in range(count):
                counters[family] += 1
                sample = _build_family_sample(
                    rng=rng,
                    family=family,
                    split=split,
                    family_index=counters[family],
                    local_index=local_index,
                    used_inputs=used_inputs,
                )
                samples.append(sample)

    for index, sample in enumerate(samples, start=1):
        sample["sample_id"] = f"jm-alpha-{index:06d}"
    return samples


def write_dataset_files(output_dir: Path = OUTPUT_DIR, seed: int = SEED) -> List[Dict]:
    samples = build_dataset(seed=seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    train = [sample for sample in samples if sample["split"] == "train"]
    eval_samples = [sample for sample in samples if sample["split"] == "eval"]
    _write_jsonl(output_dir / ALL_PATH.name, samples)
    _write_jsonl(output_dir / TRAIN_PATH.name, train)
    _write_jsonl(output_dir / EVAL_PATH.name, eval_samples)
    (output_dir / REPORT_PATH.name).write_text(build_report(samples), encoding="utf-8")
    return samples


def build_report(samples: List[Dict]) -> str:
    family_counts = Counter(sample["task_family"] for sample in samples)
    route_counts = Counter(sample["route_id"] for sample in samples)
    split_counts = Counter(sample["split"] for sample in samples)
    supported_counts = Counter("supported" if sample["supported"] else "unsupported" for sample in samples)
    chinese_number_count = sum(1 for sample in samples if sample["metadata"]["contains_chinese_numbers"])
    negative_count = sum(1 for sample in samples if sample["metadata"]["contains_negative_numbers"])
    technical_count = sum(1 for sample in samples if sample["metadata"]["contains_technical_tokens"])
    eval_only_count = sum(
        1 for sample in samples
        if sample["split"] == "eval" and sample["template_id"].startswith("eval_only_")
    )
    train_signatures = {_number_signature(sample) for sample in samples if sample["split"] == "train"}
    eval_unseen_combo_count = sum(
        1 for sample in samples
        if sample["split"] == "eval" and _number_signature(sample) not in train_signatures
    )
    lines = [
        "# JianMu Chinese Intent Dataset Alpha",
        "",
        f"- dataset name: `jianmu_zh_intent_1000`",
        f"- version: `{DATASET_VERSION}`",
        f"- total samples: {len(samples)}",
        f"- train/eval split: {split_counts['train']} / {split_counts['eval']}",
        "",
        "## Task Family Counts",
        "",
        *_counter_lines(family_counts),
        "",
        "## Route ID Counts",
        "",
        *_counter_lines(route_counts),
        "",
        "## Supported vs Unsupported",
        "",
        *_counter_lines(supported_counts),
        "",
        "## Coverage",
        "",
        f"- Chinese number count: {chinese_number_count}",
        f"- negative number count: {negative_count}",
        f"- technical token count: {technical_count}",
        f"- eval-only template count: {eval_only_count}",
        f"- eval unseen number-combination count: {eval_unseen_combo_count}",
        "",
        "## Known Limitations",
        "",
        "- The dataset covers a controlled Chinese-first summation/editing slice.",
        "- Comparison samples are pre-alpha labels and are not supported by the current runtime.",
        "- Unsupported samples intentionally have no ProgramIR token sequence.",
        "- ProgramIR token labels are scaffold targets, not generated C source code.",
        "",
        "## Non-Claims",
        "",
        "- This dataset does not prove learned routing.",
        "- This dataset does not prove general program synthesis.",
        "- This dataset is a controlled Chinese-first intent-to-structure benchmark seed.",
        "- This dataset is not a natural-language generalization benchmark.",
        "",
    ]
    return "\n".join(lines)


def _build_family_sample(
    rng: random.Random,
    family: str,
    split: str,
    family_index: int,
    local_index: int,
    used_inputs: set,
) -> Dict:
    eval_only = split == "eval"
    if family == "generate_sum_program":
        return _generate_sum_sample(rng, split, family_index, local_index, used_inputs, eval_only)
    if family == "append_literal_to_existing_sum":
        return _append_literal_sample(rng, split, family_index, local_index, used_inputs, eval_only)
    if family == "append_multiple_literals_to_existing_sum":
        return _append_multiple_sample(rng, split, family_index, local_index, used_inputs, eval_only)
    if family == "replace_operand":
        return _replace_sample(rng, split, family_index, local_index, used_inputs, eval_only)
    if family == "no_op_keep_existing":
        return _noop_sample(rng, split, family_index, local_index, used_inputs, eval_only)
    if family == "explicit_expression_rewrite":
        return _rewrite_sample(rng, split, family_index, local_index, used_inputs, eval_only)
    if family == "unsupported_input":
        return _unsupported_sample(rng, split, family_index, local_index, used_inputs, eval_only)
    if family == "comparison_prealpha":
        return _comparison_sample(rng, split, family_index, local_index, used_inputs, eval_only)
    raise ValueError(family)


def _generate_sum_sample(rng, split, family_index, local_index, used_inputs, eval_only):
    values = _value_combo(rng, 2 + family_index % 3, eval_only)
    template = _select_template(
        [
            "写一个 C 程序，输出 {expr}",
            "定义{quantity_cn}个整数 {list_cn} 并输出和",
            "定义{quantity_cn}个 int，分别是 {list_cn}，然后 printf 输出和",
            "用 printf 输出 {expr}",
            "写程序计算 {expr} 的和",
            "在 main 里输出 {expr}",
        ],
        [
            "请写 C 程序：printf 输出 {expr}",
            "生成一个 main，计算 {list_cn} 的总和",
            "把 {expr} 作为整数和输出",
        ],
        family_index,
        eval_only,
    )
    input_text = _unique_input(_format_template(template, values), used_inputs, family_index)
    return _supported_sample(
        split=split,
        input_text=input_text,
        task_family="generate_sum_program",
        action="generate_new_sum_from_text",
        route_id="generate_new_sum_from_text",
        values=values,
        expected_output_provenance="generated_values",
        atomic_experts=["VariableDefinitionExpert", "SumExpressionExpert", "PrintExpert", "ConsistencyCheckExpert"],
        template_id=_template_id("gen_sum_cn", template, eval_only),
        paraphrase_group=f"gen_sum_{len(values)}_values",
        requires_previous_ir=False,
    )


def _append_literal_sample(rng, split, family_index, local_index, used_inputs, eval_only):
    previous_values = _value_combo(rng, 2 + family_index % 2, eval_only)
    value = _single_value(rng, family_index, eval_only, allow_negative=True)
    template = _select_template(
        ["再加一个 {value}", "再加一个{value_cn}", "多加一个 {value}", "追加一个 {value}", "在原来的和里再加 {value}"],
        ["继续追加一个 {value_cn}", "给当前求和再补一个 {value}", "原表达式后面加上 {value}"],
        family_index,
        eval_only,
    )
    input_text = _unique_input(_format_template(template, [value]), used_inputs, family_index)
    values = previous_values + [value]
    sample = _supported_sample(
        split=split,
        input_text=input_text,
        task_family="append_literal_to_existing_sum",
        action="expand_sum_program",
        route_id="append_literal_to_existing_sum",
        values=values,
        expected_output_provenance="previous_ir_append",
        atomic_experts=["ExpandSumExpert", "ConsistencyCheckExpert"],
        template_id=_template_id("append_one_cn", template, eval_only),
        paraphrase_group="append_single_literal",
        requires_previous_ir=True,
    )
    sample["slots"]["previous_values"] = previous_values
    sample["slots"]["append_values"] = [value]
    return sample


def _append_multiple_sample(rng, split, family_index, local_index, used_inputs, eval_only):
    previous_values = _value_combo(rng, 2, eval_only)
    if family_index % 2 == 0:
        append_values = [_single_value(rng, family_index, eval_only), _single_value(rng, family_index + 1, eval_only)]
    else:
        count = 2 + family_index % 2
        append_values = [_single_value(rng, family_index, eval_only)] * count
    template = _select_template(
        ["再加两个 {value}", "多加三个 {value}", "再追加 {pair}", "把 {pair_cn} 也加进去"],
        ["继续把 {pair} 加进当前和", "原来的表达式再追加 {pair_cn}"],
        family_index,
        eval_only,
    )
    input_text = _unique_input(_format_template(template, append_values), used_inputs, family_index)
    values = previous_values + append_values
    sample = _supported_sample(
        split=split,
        input_text=input_text,
        task_family="append_multiple_literals_to_existing_sum",
        action="expand_sum_program",
        route_id="append_multiple_literals_to_existing_sum",
        values=values,
        expected_output_provenance="previous_ir_append",
        atomic_experts=["ExpandSumExpert", "ConsistencyCheckExpert"],
        template_id=_template_id("append_multi_cn", template, eval_only),
        paraphrase_group="append_multiple_literals",
        requires_previous_ir=True,
    )
    sample["slots"]["previous_values"] = previous_values
    sample["slots"]["append_values"] = append_values
    return sample


def _replace_sample(rng, split, family_index, local_index, used_inputs, eval_only):
    previous_values = _value_combo(rng, 3, eval_only)
    replacement = _single_value(rng, family_index + 3, eval_only)
    target_index = family_index % len(previous_values)
    template = _select_template(
        ["把最后一个 {old} 改成 {new}", "把第二个数改成 {new}", "将第一个数字换成 {new}", "把 {old} 替换为 {new}"],
        ["把第{target_cn}个操作数改为 {new}", "把当前位置 {old} 换成 {new}"],
        family_index,
        eval_only,
    )
    old = previous_values[-1] if "最后" in template else previous_values[target_index]
    input_text = _unique_input(
        template.format(old=_num_text(old), new=_num_text(replacement), target_cn=_ordinal_cn(target_index)),
        used_inputs,
        family_index,
    )
    values = list(previous_values)
    values[target_index] = replacement
    route_id = "replace_last_operand" if "最后" in template else "replace_operand_by_index"
    sample = _supported_sample(
        split=split,
        input_text=input_text,
        task_family="replace_operand",
        action="replace_last_operand" if route_id == "replace_last_operand" else "replace_operand_by_index",
        route_id=route_id,
        values=values,
        expected_output_provenance="previous_ir_replace",
        atomic_experts=["ReplaceOperandExpert", "ConsistencyCheckExpert"],
        template_id=_template_id("replace_cn", template, eval_only),
        paraphrase_group="replace_operand",
        requires_previous_ir=True,
    )
    sample["slots"]["previous_values"] = previous_values
    sample["slots"]["target_operand"] = target_index
    sample["slots"]["replacement_value"] = replacement
    sample["metadata"]["whether_supported_by_current_runtime"] = route_id == "replace_last_operand"
    return sample


def _noop_sample(rng, split, family_index, local_index, used_inputs, eval_only):
    previous_values = _value_combo(rng, 2 + family_index % 2, eval_only)
    template = _select_template(
        ["不要多加 {value}，保持不变", "别改，保持原样", "不用修改", "不要替换最后一个数", "保持当前程序"],
        ["不要动当前求和", "保持原来的输出", "别加也别改"],
        family_index,
        eval_only,
    )
    value = _single_value(rng, family_index, eval_only)
    input_text = _unique_input(_format_template(template, [value]), used_inputs, family_index)
    sample = _supported_sample(
        split=split,
        input_text=input_text,
        task_family="no_op_keep_existing",
        action="keep_existing_program",
        route_id="no_op_keep_existing",
        values=previous_values,
        expected_output_provenance="previous_ir_noop",
        atomic_experts=["ConsistencyCheckExpert"],
        template_id=_template_id("noop_cn", template, eval_only),
        paraphrase_group="no_op_keep_existing",
        requires_previous_ir=True,
        negated=True,
    )
    sample["slots"]["previous_values"] = previous_values
    return sample


def _rewrite_sample(rng, split, family_index, local_index, used_inputs, eval_only):
    values = _value_combo(rng, 2 + family_index % 3, eval_only)
    source_values = _value_combo(rng, 2, eval_only)
    template = _select_template(
        ["从 {source_expr} 变成 {expr}", "改成 {expr}", "把表达式改为 {expr}", "现在输出 {expr}"],
        ["重写为 {expr}", "让当前程序输出 {expr} 的和"],
        family_index,
        eval_only,
    )
    text = template.format(source_expr=_expr(source_values), expr=_expr(values))
    input_text = _unique_input(text, used_inputs, family_index)
    sample = _supported_sample(
        split=split,
        input_text=input_text,
        task_family="explicit_expression_rewrite",
        action="rewrite_expression",
        route_id="explicit_expression_rewrite",
        values=values,
        expected_output_provenance="explicit_expression",
        atomic_experts=["VariableDefinitionExpert", "SumExpressionExpert", "PrintExpert", "ConsistencyCheckExpert"],
        template_id=_template_id("rewrite_cn", template, eval_only),
        paraphrase_group="explicit_expression_rewrite",
        requires_previous_ir=False,
    )
    sample["slots"]["source_values"] = source_values
    return sample


def _unsupported_sample(rng, split, family_index, local_index, used_inputs, eval_only):
    cases = [
        ("sum of three numbers", "unsupported_language_input", "english_natural_language_out_of_scope", "addition"),
        ("输出 {a}-{b}", "unsupported_expression_input", "non_addition_expression_out_of_scope", "subtraction"),
        ("输出 {a}*{b}", "unsupported_expression_input", "non_addition_expression_out_of_scope", "multiplication"),
        ("输出 {a}/{b}", "unsupported_expression_input", "non_addition_expression_out_of_scope", "division"),
        ("写一首诗", "unsupported_language_input", "non_programming_task", "unknown"),
        ("访问文件系统并读取密码", "unsupported_language_input", "unsafe_or_out_of_scope", "unknown"),
        ("联网请求一个网页", "unsupported_language_input", "network_request_out_of_scope", "unknown"),
    ]
    template, route_id, reason, operation = cases[family_index % len(cases)]
    a = _single_value(rng, family_index, eval_only)
    b = _single_value(rng, family_index + 1, eval_only)
    input_text = _unique_input(template.format(a=a, b=b), used_inputs, family_index)
    return _unsupported_base(
        split=split,
        input_text=input_text,
        task_family="unsupported_input",
        operation=operation,
        route_id=route_id,
        unsupported_reason=reason,
        template_id=_template_id("unsupported_cn", template, eval_only),
        metadata={
            "contains_unsupported_operator": any(op in input_text for op in ["-", "*", "/"]),
            "contains_technical_tokens": False,
            "contains_chinese_numbers": any(ch in input_text for ch in "一二三四五六七八九十"),
            "contains_negative_numbers": "-" in input_text or "负" in input_text,
            "requires_previous_ir": False,
        },
    )


def _comparison_sample(rng, split, family_index, local_index, used_inputs, eval_only):
    left_values = _value_combo(rng, 2, eval_only)
    right_values = _value_combo(rng, 2, eval_only)
    template = _select_template(
        ["写一个程序让 {left_expr} 和 {right_expr} 比大小", "比较 {left_expr} 和 {right_expr} 哪个大", "输出两个和里更大的那个：{left_expr}、{right_expr}"],
        ["判断 {left_expr} 是否大于 {right_expr}", "比较两边求和结果：{left_expr} 对 {right_expr}"],
        family_index,
        eval_only,
    )
    input_text = _unique_input(
        template.format(left_expr=_expr(left_values), right_expr=_expr(right_values)),
        used_inputs,
        family_index,
    )
    sample = _unsupported_base(
        split=split,
        input_text=input_text,
        task_family="comparison_prealpha",
        operation="comparison",
        route_id="unsupported_expression_input",
        unsupported_reason="comparison_not_supported_in_v0_5_6",
        template_id=_template_id("comparison_future_cn", template, eval_only),
        metadata={
            "contains_unsupported_operator": False,
            "contains_technical_tokens": "程序" in input_text,
            "contains_chinese_numbers": False,
            "contains_negative_numbers": any(value < 0 for value in left_values + right_values),
            "requires_previous_ir": False,
        },
    )
    sample["slots"]["left_values"] = left_values
    sample["slots"]["right_values"] = right_values
    return sample


def _supported_sample(
    split: str,
    input_text: str,
    task_family: str,
    action: str,
    route_id: str,
    values: List[int],
    expected_output_provenance: str,
    atomic_experts: List[str],
    template_id: str,
    paraphrase_group: str,
    requires_previous_ir: bool,
    negated: bool = False,
) -> Dict:
    return {
        "sample_id": "",
        "split": split,
        "input_text": input_text,
        "language": "zh-CN",
        "task_family": task_family,
        "intent": {
            "domain": "arithmetic",
            "mode": "edit" if requires_previous_ir else "generate",
            "operation": "addition",
            "action": action,
        },
        "slots": {
            "values": values,
            "quantity": len(values),
            "target_operand": None,
            "replacement_value": None,
            "negated": negated,
        },
        "route_id": route_id,
        "atomic_experts": atomic_experts,
        "program_ir_tokens": _sum_tokens(values),
        "expected_output": f"{sum(values)}\n",
        "expected_output_provenance": expected_output_provenance,
        "supported": True,
        "unsupported_reason": None,
        "difficulty": _difficulty(values),
        "template_id": template_id,
        "paraphrase_group": paraphrase_group,
        "metadata": _metadata(input_text, values, requires_previous_ir),
    }


def _unsupported_base(
    split: str,
    input_text: str,
    task_family: str,
    operation: str,
    route_id: str,
    unsupported_reason: str,
    template_id: str,
    metadata: Dict,
) -> Dict:
    return {
        "sample_id": "",
        "split": split,
        "input_text": input_text,
        "language": "zh-CN",
        "task_family": task_family,
        "intent": {
            "domain": "arithmetic" if operation != "unknown" else "unknown",
            "mode": "unsupported",
            "operation": operation,
            "action": "unsupported_input",
        },
        "slots": {
            "values": [],
            "quantity": None,
            "target_operand": None,
            "replacement_value": None,
            "negated": False,
        },
        "route_id": route_id,
        "atomic_experts": [],
        "program_ir_tokens": [],
        "expected_output": None,
        "expected_output_provenance": "none",
        "supported": False,
        "unsupported_reason": unsupported_reason,
        "difficulty": "unsupported",
        "template_id": template_id,
        "paraphrase_group": task_family,
        "metadata": metadata,
    }


def _sum_tokens(values: List[int]) -> List[Dict]:
    tokens = [{"type": "INCLUDE_STDIO"}, {"type": "MAIN_BEGIN"}]
    tokens.extend({"type": "LITERAL_INT", "value": value} for value in values)
    tokens.extend([{"type": "ADD_REDUCE"}, {"type": "PRINT_EXPR"}, {"type": "MAIN_END"}])
    return tokens


def _metadata(input_text: str, values: List[int], requires_previous_ir: bool) -> Dict:
    return {
        "requires_previous_ir": requires_previous_ir,
        "contains_technical_tokens": bool(any(token in input_text for token in ["C", "int", "printf", "main"])),
        "contains_chinese_numbers": any(token in input_text for token in CHINESE_NUMBERS.values() if not token.startswith("-")),
        "contains_negative_numbers": any(value < 0 for value in values) or "负" in input_text,
        "contains_unsupported_operator": any(op in input_text for op in ["-", "*", "/"]) and not any(value < 0 for value in values),
    }


def _value_combo(rng: random.Random, length: int, eval_only: bool) -> List[int]:
    if eval_only:
        pool = [6, 7, 8, 9, 10, 20, -1, -2, -3]
    else:
        pool = [1, 2, 3, 4, 5, 10, -1, -2]
    return [pool[(rng.randrange(len(pool)) + index) % len(pool)] for index in range(length)]


def _single_value(rng: random.Random, index: int, eval_only: bool, allow_negative: bool = False) -> int:
    pool = [6, 7, 8, 9, 10, 20, -1, -2, -3] if eval_only else [1, 2, 3, 4, 5, 10, -1, -2]
    if not allow_negative:
        pool = [value for value in pool if value > 0]
    return pool[(rng.randrange(len(pool)) + index) % len(pool)]


def _select_template(train_templates: List[str], eval_templates: List[str], index: int, eval_only: bool) -> str:
    templates = eval_templates if eval_only else train_templates
    return templates[index % len(templates)]


def _template_id(prefix: str, template: str, eval_only: bool) -> str:
    normalized = int(hashlib.sha1(template.encode("utf-8")).hexdigest()[:8], 16) % 1000
    marker = "eval_only" if eval_only else "train"
    return f"{marker}_{prefix}_{normalized:03d}"


def _format_template(template: str, values: List[int]) -> str:
    return template.format(
        value=_num_text(values[0]),
        value_cn=_num_text(values[0], prefer_cn=True),
        pair=" 和 ".join(_num_text(value) for value in values[:2]),
        pair_cn=" 和 ".join(_num_text(value, prefer_cn=True) for value in values[:2]),
        expr=_expr(values),
        list_cn="、".join(_num_text(value, prefer_cn=value > 0) for value in values),
        quantity_cn=_quantity_cn(len(values)),
    )


def _unique_input(input_text: str, used_inputs: set, index: int) -> str:
    candidate = input_text
    suffix = 1
    while candidate in used_inputs:
        candidate = f"{input_text}（变体{index}-{suffix}）"
        suffix += 1
    used_inputs.add(candidate)
    return candidate


def _expr(values: Iterable[int]) -> str:
    return " + ".join(_num_text(value, prefer_cn=value in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)) for value in values)


def _num_text(value: int, prefer_cn: bool = False) -> str:
    if prefer_cn and value in CHINESE_NUMBERS:
        return CHINESE_NUMBERS[value]
    return str(value)


def _quantity_cn(quantity: int) -> str:
    return CHINESE_NUMBERS.get(quantity, str(quantity))


def _ordinal_cn(index: int) -> str:
    return ["一", "二", "三", "四", "五"][index] if index < 5 else str(index + 1)


def _difficulty(values: List[int]) -> str:
    if any(value < 0 for value in values):
        return "medium"
    if len(values) > 3:
        return "medium"
    return "easy"


def _counter_lines(counter: Counter) -> List[str]:
    return [f"- {key}: {counter[key]}" for key in sorted(counter)]


def _write_jsonl(path: Path, samples: List[Dict]):
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False, sort_keys=True) + "\n")


def _number_signature(sample: Dict) -> Tuple:
    slots = sample.get("slots", {})
    if "left_values" in slots or "right_values" in slots:
        return tuple(slots.get("left_values", [])), tuple(slots.get("right_values", []))
    return tuple(slots.get("values") or [])


if __name__ == "__main__":
    write_dataset_files()
