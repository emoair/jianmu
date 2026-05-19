import argparse
import json
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


SOURCE_GENERATOR = "v0.6.8 Large Architecture-Aligned Dataset（大规模架构对齐数据集）"
DEFAULT_SEED = 42


@dataclass(frozen=True)
class TargetSpec:
    group_id: str
    canonical: str
    expected_output: str
    expr: str
    chinese_expr: str
    expression_family: str
    structure_policy: str
    numbers: Tuple[int, ...]
    operators: Tuple[str, ...]
    has_parentheses: bool = False
    contains_negative_number: bool = False


def build_large_architecture_aligned_dataset(size: int = 6000, seed: int = DEFAULT_SEED) -> Dict[str, List[Dict]]:
    """Build deterministic Architecture-Aligned Dataset（架构对齐数据集） splits."""
    rng = random.Random(seed)
    counts = _split_counts(size)
    train_specs = _make_supported_specs(rng, counts["train_supported"] // 6, prefix="seen")
    unseen_specs = _make_supported_specs(rng, max(1, counts["eval_unseen_supported"] // 6), prefix="unseen", existing={s.canonical for s in train_specs})

    splits = {
        "train": [],
        "eval_seen_target_unseen_paraphrase": [],
        "eval_unseen_target": [],
        "eval_ood": [],
    }
    sample_counter = 1
    for spec in train_specs:
        variants = _supported_variants(spec)
        for variant in variants[:6]:
            splits["train"].append(_sample(sample_counter, "train", spec, variant, seed))
            sample_counter += 1
        splits["eval_seen_target_unseen_paraphrase"].append(
            _sample(sample_counter, "eval_seen_target_unseen_paraphrase", spec, variants[6], seed)
        )
        sample_counter += 1

    for spec in unseen_specs:
        for variant in _supported_variants(spec)[:6]:
            splits["eval_unseen_target"].append(_sample(sample_counter, "eval_unseen_target", spec, variant, seed))
            sample_counter += 1

    splits["train"].extend(_unsupported_samples(sample_counter, counts["train_unsupported"], "train", seed, rng))
    sample_counter += counts["train_unsupported"]
    splits["eval_ood"].extend(_unsupported_samples(sample_counter, counts["eval_ood"], "eval_ood", seed, rng))

    return _dedupe_global_splits(splits)


def write_large_architecture_aligned_dataset(size: int, seed: int, out_dir: Path) -> Dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    splits = build_large_architecture_aligned_dataset(size=size, seed=seed)
    all_samples = []
    for split_name in ["train", "eval_seen_target_unseen_paraphrase", "eval_unseen_target", "eval_ood"]:
        path = out_dir / f"jianmu_v0_6_8_{split_name}.jsonl"
        _write_jsonl(path, splits[split_name])
        all_samples.extend(splits[split_name])
    all_path = out_dir / "jianmu_v0_6_8_all.jsonl"
    _write_jsonl(all_path, all_samples)
    quality = validate_large_dataset(all_samples)
    manifest = dataset_manifest(all_samples, size=size, seed=seed, quality=quality)
    (out_dir / "jianmu_v0_6_8_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (out_dir / "jianmu_v0_6_8_report.md").write_text(dataset_report_markdown(all_samples, quality), encoding="utf-8")
    return manifest


def load_jsonl(path: Path) -> List[Dict]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def validate_large_dataset(samples: List[Dict]) -> Dict:
    errors = []
    ids = [sample["sample_id"] for sample in samples]
    texts = [sample["input_text"] for sample in samples]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_sample_id")
    if len(texts) != len(set(texts)):
        errors.append("duplicate_input_text")
    for sample in samples:
        language_target = _target_option(sample, "language_target")
        if sample["supported"]:
            if not sample.get("target_ir_canonical"):
                errors.append(f"supported_missing_targetir:{sample['sample_id']}")
            if sample.get("expected_output") is None:
                errors.append(f"supported_missing_expected_output:{sample['sample_id']}")
            if language_target == "unknown":
                errors.append(f"supported_language_unknown:{sample['sample_id']}")
            if sample["input_mode"] == "math_expression" and language_target != "math_expression_context":
                errors.append(f"math_expression_bad_language_target:{sample['sample_id']}")
            if sample["input_mode"] in {"zh_natural", "zh_technical_mixed", "implicit_c", "explicit_c", "zh_number_expression"} and not _contains_chinese(sample["input_text"]):
                if sample["input_mode"] not in {"math_expression"}:
                    errors.append(f"zh_mode_without_chinese:{sample['sample_id']}")
        if sample["input_mode"] == "ood_english" and sample["supported"]:
            errors.append(f"ood_english_supported:{sample['sample_id']}")
        if sample["input_mode"] == "unsupported_arithmetic" and sample["supported"]:
            errors.append(f"unsupported_arithmetic_supported:{sample['sample_id']}")

    train_groups = {sample["paraphrase_group"] for sample in samples if sample["split"] == "train" and sample["supported"]}
    unseen_groups = {sample["paraphrase_group"] for sample in samples if sample["split"] == "eval_unseen_target" and sample["supported"]}
    group_leakage = sorted(train_groups & unseen_groups)
    if group_leakage:
        errors.append("train_eval_unseen_target_group_leakage")
    train_texts = {sample["input_text"] for sample in samples if sample["split"] == "train"}
    seen_eval_texts = {sample["input_text"] for sample in samples if sample["split"] == "eval_seen_target_unseen_paraphrase"}
    if train_texts & seen_eval_texts:
        errors.append("eval_seen_text_leakage")

    groups = defaultdict(list)
    for sample in samples:
        if sample["supported"]:
            groups[sample["paraphrase_group"]].append(sample)
    for group_id, group_samples in groups.items():
        if len(group_samples) < 4:
            errors.append(f"small_supported_group:{group_id}")
        canonicals = {sample["target_ir_canonical"] for sample in group_samples}
        if len(canonicals) != 1:
            errors.append(f"group_targetir_mismatch:{group_id}")

    expression_counts = Counter(sample.get("expression_family") for sample in samples if sample["supported"])
    dominant = max(expression_counts.values(), default=0)
    supported_count = sum(1 for sample in samples if sample["supported"])
    if supported_count and dominant / supported_count > 0.55:
        errors.append("expression_family_distribution_too_single")
    unsupported_count = len(samples) - supported_count
    ood_ratio = unsupported_count / max(len(samples), 1)
    if not 0.1 <= ood_ratio <= 0.35:
        errors.append("ood_ratio_out_of_range")

    duplicate_input_count = len(texts) - len(set(texts))
    return {
        "valid": not errors,
        "errors": errors,
        "duplicate_input_count": duplicate_input_count,
        "train_eval_unseen_target_group_leakage_count": len(group_leakage),
        "train_eval_unseen_target_group_leakage": group_leakage[:20],
        "eval_seen_input_text_leakage_count": len(train_texts & seen_eval_texts),
        "language_target_unknown_count": sum(1 for sample in samples if _target_option(sample, "language_target") == "unknown"),
        "ood_english_supported_count": sum(1 for sample in samples if sample["input_mode"] == "ood_english" and sample["supported"]),
    }


def dataset_manifest(samples: List[Dict], size: int, seed: int, quality: Dict) -> Dict:
    supported = [sample for sample in samples if sample["supported"]]
    split_counts = Counter(sample["split"] for sample in samples)
    group_counts = Counter(sample["paraphrase_group"] for sample in supported)
    return {
        "dataset_name": "JianMu v0.6.8 Large Architecture-Aligned Dataset（大规模架构对齐数据集）",
        "requested_size": size,
        "actual_total": len(samples),
        "seed": seed,
        "split_counts": dict(split_counts),
        "supported_count": len(supported),
        "unsupported_count": len(samples) - len(supported),
        "input_mode_counts": dict(Counter(sample["input_mode"] for sample in samples)),
        "expression_family_counts": _string_key_counts(Counter(sample.get("expression_family") for sample in supported)),
        "structure_policy_counts": _string_key_counts(Counter(sample.get("structure_policy") for sample in supported)),
        "language_target_distribution": _string_key_counts(Counter(_target_option(sample, "language_target") for sample in samples)),
        "paraphrase_group_count": len(group_counts),
        "average_paraphrases_per_group": round(sum(group_counts.values()) / max(len(group_counts), 1), 4),
        "quality": quality,
    }


def dataset_report_markdown(samples: List[Dict], quality: Dict) -> str:
    manifest = dataset_manifest(samples, size=len(samples), seed=samples[0]["generator_seed"] if samples else DEFAULT_SEED, quality=quality)
    lines = [
        "# v0.6.8 Large Architecture-Aligned Dataset（大规模架构对齐数据集） Report",
        "",
        "This deterministic local dataset supports Scale Smoke Benchmark（规模化冒烟基准） diagnostics for BranchChain（分支链）, Confidence-Gated Continuation（置信度守卫式继续）, AtomicSynthesis（原子结构合成）, and TargetIR（目标中间表示） regeneration.",
        "",
        "## Summary（摘要）",
        "",
        f"- total samples: {manifest['actual_total']}",
        f"- split counts: {manifest['split_counts']}",
        f"- supported / unsupported: {manifest['supported_count']} / {manifest['unsupported_count']}",
        f"- paraphrase_group count（复述组数量）: {manifest['paraphrase_group_count']}",
        f"- average paraphrases per group（平均复述数）: {manifest['average_paraphrases_per_group']}",
        "",
        "## Distributions（分布）",
        "",
        f"- input_mode counts: {manifest['input_mode_counts']}",
        f"- expression_family counts: {manifest['expression_family_counts']}",
        f"- structure_policy counts: {manifest['structure_policy_counts']}",
        f"- language_target distribution: {manifest['language_target_distribution']}",
        "",
        "## Dataset Leakage Check（数据泄漏检查）",
        "",
        f"- duplicate input count: {quality['duplicate_input_count']}",
        f"- train/eval_unseen_target group leakage: {quality['train_eval_unseen_target_group_leakage_count']}",
        f"- eval_seen_target_unseen_paraphrase input leakage: {quality['eval_seen_input_text_leakage_count']}",
        f"- language_target=unknown count: {quality['language_target_unknown_count']}",
        f"- OOD English supported count（英语分布外正样本数）: {quality['ood_english_supported_count']}",
        f"- valid: {quality['valid']}",
        "",
        "## Examples（样例）",
        "",
    ]
    for mode, sample in _first_by(samples, "input_mode").items():
        lines.append(f"- {mode}: {sample['input_text']} -> {sample.get('target_ir_canonical')}")
    lines.extend(
        [
            "",
            "## Non-Claims（非主张）",
            "",
            "- This does not prove stable DarwinForge（达尔文进化炉） convergence.",
            "- This does not prove general program synthesis.",
            "- This does not train C source text.",
            "- This does not patch old source code.",
            "- This does not prove AGI, Transformer replacement, or hardware BPU implementation.",
            "- This is a deterministic local dataset generation and Scale Smoke Benchmark（规模化冒烟基准） experiment.",
        ]
    )
    return "\n".join(lines) + "\n"


def _split_counts(size: int) -> Dict[str, int]:
    if size < 80:
        raise ValueError("size must be at least 80")
    units = max(1, size // 60)
    return {
        "train_supported": units * 36,
        "train_unsupported": units * 6,
        "eval_seen_supported": units * 6,
        "eval_unseen_supported": units * 6,
        "eval_ood": units * 6,
    }


def _make_supported_specs(rng: random.Random, count: int, prefix: str, existing: Optional[set] = None) -> List[TargetSpec]:
    existing = set(existing or set())
    specs = []
    attempts = 0
    while len(specs) < count and attempts < count * 200:
        attempts += 1
        family = rng.choice([
            "addition",
            "subtraction",
            "multiplication",
            "exact_division",
            "addition_chain",
            "mixed_precedence",
            "parentheses",
            "negative",
        ])
        spec = _random_spec(rng, family, prefix, len(specs) + 1)
        if spec.canonical in existing:
            continue
        existing.add(spec.canonical)
        specs.append(spec)
    if len(specs) < count:
        raise RuntimeError("could not generate enough unique TargetIR groups")
    return specs


def _random_spec(rng: random.Random, family: str, prefix: str, index: int) -> TargetSpec:
    if family == "addition":
        a, b = _nums(rng, 2)
        canonical, value, expr, zh = f"add(lit({a}),lit({b}))", a + b, f"{a}+{b}", f"{_zh(a)}加{_zh(b)}"
        structure = "binary_operation"
        ops = ("+",)
    elif family == "subtraction":
        a, b = _nums(rng, 2)
        canonical, value, expr, zh = f"sub(lit({a}),lit({b}))", a - b, f"{a}-{b}", f"{_zh(a)}减{_zh(b)}"
        structure = "binary_operation"
        ops = ("-",)
    elif family == "multiplication":
        a, b = _nums(rng, 2)
        canonical, value, expr, zh = f"mul(lit({a}),lit({b}))", a * b, f"{a}*{b}", f"{_zh(a)}乘{_zh(b)}"
        structure = "binary_operation"
        ops = ("*",)
    elif family == "exact_division":
        b = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        q = rng.randint(-8, 12)
        a = b * q
        canonical, value, expr, zh = f"div(lit({a}),lit({b}))", q, f"{a}/{b}", f"{_zh(a)}除以{_zh(b)}"
        structure = "binary_operation"
        ops = ("/",)
    elif family == "addition_chain":
        a, b, c = _nums(rng, 3)
        canonical, value, expr, zh = f"add(add(lit({a}),lit({b})),lit({c}))", a + b + c, f"{a}+{b}+{c}", f"{_zh(a)}加{_zh(b)}加{_zh(c)}"
        structure = "reduce_chain"
        ops = ("+", "+")
    elif family == "mixed_precedence":
        a, b, c = _nums(rng, 3)
        if rng.random() < 0.5:
            canonical, value, expr, zh = f"add(lit({a}),mul(lit({b}),lit({c})))", a + b * c, f"{a}+{b}*{c}", f"{_zh(a)}加{_zh(b)}乘{_zh(c)}"
            ops = ("+", "*")
        else:
            canonical, value, expr, zh = f"add(mul(lit({a}),lit({b})),lit({c}))", a * b + c, f"{a}*{b}+{c}", f"{_zh(a)}乘{_zh(b)}加{_zh(c)}"
            ops = ("*", "+")
        structure = "precedence_tree"
    elif family == "parentheses":
        a, b, c = _nums(rng, 3)
        if rng.random() < 0.7:
            canonical, value, expr, zh = f"mul(add(lit({a}),lit({b})),lit({c}))", (a + b) * c, f"({a}+{b})*{c}", f"括号里{_zh(a)}加{_zh(b)}再乘{_zh(c)}"
            ops = ("+", "*")
        else:
            c = rng.choice([1, 2, 3, 4, 5])
            b = rng.randint(-10, 20)
            q = rng.randint(-5, 8)
            a = b + c * q
            canonical, value, expr, zh = f"div(sub(lit({a}),lit({b})),lit({c}))", q, f"({a}-{b})/{c}", f"括号里{_zh(a)}减{_zh(b)}再除以{_zh(c)}"
            ops = ("-", "/")
        structure = "parenthesized_tree"
    else:
        a = -rng.randint(1, 20)
        b = rng.randint(1, 50)
        op = rng.choice(["+", "-", "*"])
        if op == "+":
            canonical, value, expr, zh = f"add(lit({a}),lit({b}))", a + b, f"{a}+{b}", f"{_zh(a)}加{_zh(b)}"
            family = "addition"
        elif op == "-":
            canonical, value, expr, zh = f"sub(lit({a}),lit({b}))", a - b, f"{a}-{b}", f"{_zh(a)}减{_zh(b)}"
            family = "subtraction"
        else:
            canonical, value, expr, zh = f"mul(lit({a}),lit({b}))", a * b, f"{a}*{b}", f"{_zh(a)}乘{_zh(b)}"
            family = "multiplication"
        structure = "binary_operation"
        ops = (op,)
    return TargetSpec(
        group_id=f"{prefix}_{_slug(family)}_{index:05d}",
        canonical=canonical,
        expected_output=f"{value}\n",
        expr=expr,
        chinese_expr=zh,
        expression_family=family,
        structure_policy=structure,
        numbers=tuple(_numbers_from_canonical(canonical)),
        operators=ops,
        has_parentheses="(" in expr,
        contains_negative_number="lit(-" in canonical,
    )


def _supported_variants(spec: TargetSpec) -> List[Tuple[str, str, str]]:
    expr_spaced = " ".join(_expr_tokens(spec.expr))
    return [
        (f"写一个 C 程序输出 {spec.expr}", "explicit_c", "explicit_C"),
        (f"写一个 C 程序，printf 输出 {spec.expr}", "zh_technical_mixed", "explicit_C"),
        (f"在 main 里输出 {spec.expr}", "zh_technical_mixed", "explicit_C"),
        (f"输出 {spec.expr}", "implicit_c", "implicit_C"),
        (f"计算 {expr_spaced} 并输出", "zh_natural", "implicit_C"),
        (spec.expr, "math_expression", "math_expression_context"),
        (f"{spec.chinese_expr}等于多少", "zh_number_expression", "math_expression_context"),
    ]


def _sample(counter: int, split: str, spec: TargetSpec, variant: Tuple[str, str, str], seed: int) -> Dict:
    text, input_mode, language_target = variant
    return {
        "sample_id": f"jm-v068-{counter:06d}",
        "input_text": text,
        "input_mode": input_mode,
        "split": split,
        "paraphrase_group": spec.group_id,
        "target_branch_path": [
            ["task_scope", "programming"],
            ["language_target", language_target],
            ["semantic_domain", "arithmetic"],
            ["arithmetic_family", _family_label(spec.expression_family)],
            ["structure_policy", spec.structure_policy],
            ["slot_binding_policy", "signed_number_order" if spec.contains_negative_number else "surface_number_order"],
            ["target_builder", "canonical_arithmetic_targetir"],
        ],
        "target_ir_canonical": spec.canonical,
        "expected_output": spec.expected_output,
        "supported": True,
        "unsupported_reason": None,
        "expression_family": _family_label(spec.expression_family),
        "structure_policy": spec.structure_policy,
        "operator_count": len(spec.operators),
        "number_count": len(spec.numbers),
        "has_parentheses": spec.has_parentheses,
        "uses_chinese_numerals": input_mode == "zh_number_expression",
        "contains_negative_number": spec.contains_negative_number,
        "source_generator": SOURCE_GENERATOR,
        "generator_seed": seed,
    }


def _unsupported_samples(start: int, count: int, split: str, seed: int, rng: random.Random) -> List[Dict]:
    samples = []
    builders = [_unsupported_english, _unsupported_unrelated, _unsupported_arithmetic, _unsupported_comparison]
    for offset in range(count):
        builder = builders[offset % len(builders)]
        samples.append(builder(start + offset, split, seed, rng, offset))
    return samples


def _unsupported_english(counter: int, split: str, seed: int, rng: random.Random, offset: int) -> Dict:
    templates = [
        "calculate {a} plus {b}",
        "sum of {a} and {b}",
        "write a C program to output {a}+{b}",
        "print the result of {a} times {b}",
    ]
    a, b = rng.randint(1, 50), rng.randint(1, 50)
    text = templates[offset % len(templates)].format(a=a, b=b)
    return _unsupported_sample(counter, text, "ood_english", split, "unsupported_language", [["task_scope", "programming"], ["language_target", "reject_unsupported_language"]], seed)


def _unsupported_unrelated(counter: int, split: str, seed: int, rng: random.Random, offset: int) -> Dict:
    texts = [
        f"写一首关于数字 {rng.randint(1, 50)} 的诗",
        f"联网下载第 {rng.randint(1, 50)} 个文件",
        f"帮我查天气 {rng.randint(1, 50)} 分钟后",
        f"删除本地第 {rng.randint(1, 50)} 个临时文件",
    ]
    reason = "unsupported_non_programming" if offset % 2 == 0 else "unsupported_out_of_scope"
    target = "reject_non_programming" if reason == "unsupported_non_programming" else "reject_out_of_scope"
    return _unsupported_sample(counter, texts[offset % len(texts)], "ood_unrelated", split, reason, [["task_scope", target]], seed)


def _unsupported_arithmetic(counter: int, split: str, seed: int, rng: random.Random, offset: int) -> Dict:
    if offset % 3 == 0:
        a, b = rng.choice([5, 7, 11, 13, 17]), rng.choice([2, 3, 4, 6])
        if a % b == 0:
            a += 1
        text, reason = f"输出 {a}/{b}", "division_not_exact"
    elif offset % 3 == 1:
        text, reason = f"计算 {rng.randint(1, 50)}/0 并输出", "division_by_zero"
    else:
        text, reason = f"输出 ((({rng.randint(1, 9)}+{rng.randint(1, 9)}))) + {rng.randint(1, 9)} 的深层括号版本", "unsupported_depth"
    target = [
        ["task_scope", "programming"],
        ["language_target", "implicit_C"],
        ["semantic_domain", "arithmetic"],
        ["arithmetic_family", "unsupported"],
    ]
    return _unsupported_sample(counter, text, "unsupported_arithmetic", split, reason, target, seed)


def _unsupported_comparison(counter: int, split: str, seed: int, rng: random.Random, offset: int) -> Dict:
    a, b, c, d = rng.randint(1, 20), rng.randint(1, 20), rng.randint(1, 20), rng.randint(1, 20)
    text = f"请比较 {a}+{b} 和 {c}+{d} 哪个大"
    target = [["task_scope", "programming"], ["language_target", "implicit_C"], ["semantic_domain", "comparison_future"]]
    return _unsupported_sample(counter, text, "comparison_future", split, "comparison_not_supported_in_v0_6_8", target, seed)


def _unsupported_sample(counter: int, text: str, input_mode: str, split: str, reason: str, target_path: List[List[str]], seed: int) -> Dict:
    return {
        "sample_id": f"jm-v068-{counter:06d}",
        "input_text": text,
        "input_mode": input_mode,
        "split": split,
        "paraphrase_group": f"{split}_{reason}_{counter:06d}",
        "target_branch_path": target_path,
        "target_ir_canonical": None,
        "expected_output": None,
        "supported": False,
        "unsupported_reason": reason,
        "expression_family": None,
        "structure_policy": None,
        "operator_count": sum(1 for ch in text if ch in "+-*/"),
        "number_count": len(re.findall(r"-?\d+", text)),
        "has_parentheses": "(" in text or ")" in text,
        "uses_chinese_numerals": any(ch in text for ch in "零一二两三四五六七八九十负"),
        "contains_negative_number": bool(re.search(r"-\d+|负[一二三四五六七八九十]", text)),
        "source_generator": SOURCE_GENERATOR,
        "generator_seed": seed,
    }


def _write_jsonl(path: Path, samples: Iterable[Dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for sample in samples:
            handle.write(json.dumps(sample, ensure_ascii=False, sort_keys=True) + "\n")


def _dedupe_preserve(samples: List[Dict]) -> List[Dict]:
    seen = set()
    result = []
    for sample in samples:
        text = sample["input_text"]
        if text in seen:
            sample = dict(sample)
            sample["input_text"] = f"{text}（样本{sample['sample_id']}）"
        seen.add(sample["input_text"])
        result.append(sample)
    return result


def _dedupe_global_splits(splits: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    seen = set()
    result = {}
    for split_name in ["train", "eval_seen_target_unseen_paraphrase", "eval_unseen_target", "eval_ood"]:
        rows = []
        for sample in splits[split_name]:
            text = sample["input_text"]
            if text in seen:
                sample = dict(sample)
                sample["input_text"] = f"{text}（{sample['sample_id']}）"
            seen.add(sample["input_text"])
            rows.append(sample)
        result[split_name] = rows
    return result


def _nums(rng: random.Random, count: int) -> Tuple[int, ...]:
    return tuple(rng.randint(1, 50) for _ in range(count))


def _numbers_from_canonical(canonical: str) -> List[int]:
    return [int(value) for value in re.findall(r"lit\((-?\d+)\)", canonical)]


def _family_label(family: str) -> str:
    if family == "addition_chain":
        return "addition"
    return family


def _zh(value: int) -> str:
    if value < 0:
        return "负" + _zh(-value)
    digits = "零一二三四五六七八九"
    if value < 10:
        return digits[value]
    if value == 10:
        return "十"
    if value < 20:
        return "十" + digits[value % 10]
    if value < 100:
        tens, ones = divmod(value, 10)
        return digits[tens] + "十" + (digits[ones] if ones else "")
    return str(value)


def _expr_tokens(expr: str) -> List[str]:
    return [token for token in re.split(r"([+\-*/()])", expr) if token and not token.isspace()]


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _target_option(sample: Dict, layer_name: str) -> Optional[str]:
    for layer, option in sample.get("target_branch_path", []):
        if layer == layer_name:
            return option
    return None


def _contains_chinese(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _first_by(samples: List[Dict], key: str) -> Dict[str, Dict]:
    result = {}
    for sample in samples:
        result.setdefault(str(sample.get(key)), sample)
    return result


def _string_key_counts(counter: Counter) -> Dict[str, int]:
    return {str(key): value for key, value in counter.items()}


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Generate JianMu v0.6.8 deterministic Architecture-Aligned Dataset（架构对齐数据集）.")
    parser.add_argument("--size", type=int, default=6000)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--out", type=Path, default=Path("datasets/v0_6_8"))
    args = parser.parse_args(argv)
    manifest = write_large_architecture_aligned_dataset(args.size, args.seed, args.out)
    print(f"dataset total: {manifest['actual_total']}")
    print(f"split counts: {manifest['split_counts']}")
    print(f"quality valid: {manifest['quality']['valid']}")
    print(f"report: {args.out / 'jianmu_v0_6_8_report.md'}")


if __name__ == "__main__":
    main()
