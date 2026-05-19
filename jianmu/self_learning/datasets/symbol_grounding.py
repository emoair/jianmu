import argparse
import json
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


SOURCE_GENERATOR = "v0.7.0 Symbol Grounding Curriculum（符号接地课程）"
DEFAULT_SEED = 42


@dataclass(frozen=True)
class GroundingSpec:
    paired_group_id: str
    curriculum_stage: str
    canonical: str
    expected_output: str
    expression_family: str
    structure_policy: str
    symbol_slots: Tuple[Dict, ...]
    operator_slots: Tuple[Dict, ...]
    arabic_expr: str
    zh_expr: str
    mixed_exprs: Tuple[str, ...]


def build_symbol_grounding_dataset(size: int = 3000, seed: int = DEFAULT_SEED) -> Dict[str, List[Dict]]:
    rng = random.Random(seed)
    counts = _split_counts(size)
    supported_total = counts["train"] + counts["eval"]
    specs = _build_specs(rng, supported_total // 4 + 8)
    samples = []
    counter = 1
    stage_cycle = ["numeral_grounding", "operator_grounding", "structure_grounding"]
    for stage in stage_cycle:
        stage_specs = [spec for spec in specs if spec.curriculum_stage == stage]
        target_count = counts[f"{stage}_samples"]
        index = 0
        while sum(1 for s in samples if s["curriculum_stage"] == stage and s["supported"]) < target_count:
            spec = stage_specs[index % len(stage_specs)]
            for text, mode in _variants(spec):
                if sum(1 for s in samples if s["curriculum_stage"] == stage and s["supported"]) >= target_count:
                    break
                split = "train" if sum(1 for s in samples if s["split"] == "train") < counts["train"] else "eval"
                samples.append(_supported_sample(counter, split, spec, text, mode, seed))
                counter += 1
            index += 1
    ood_samples = _ood_samples(counter, counts["ood"], seed, rng)
    all_samples = _dedupe(samples + ood_samples)
    return {
        "train": [sample for sample in all_samples if sample["split"] == "train"],
        "eval": [sample for sample in all_samples if sample["split"] == "eval"],
        "ood": [sample for sample in all_samples if sample["split"] == "ood"],
    }


def write_symbol_grounding_dataset(size: int, seed: int, out_dir: Path) -> Dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    splits = build_symbol_grounding_dataset(size=size, seed=seed)
    all_samples = []
    for split_name in ["train", "eval", "ood"]:
        path = out_dir / f"jianmu_v0_7_0_symbol_grounding_{split_name}.jsonl"
        _write_jsonl(path, splits[split_name])
        all_samples.extend(splits[split_name])
    _write_jsonl(out_dir / "jianmu_v0_7_0_symbol_grounding_all.jsonl", all_samples)
    manifest = manifest_for(all_samples, size=size, seed=seed)
    (out_dir / "jianmu_v0_7_0_symbol_grounding_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (out_dir / "jianmu_v0_7_0_symbol_grounding_report.md").write_text(report_markdown(manifest, all_samples), encoding="utf-8")
    return manifest


def load_symbol_grounding_split(dataset_dir: Path, split: str) -> List[Dict]:
    return load_jsonl(dataset_dir / f"jianmu_v0_7_0_symbol_grounding_{split}.jsonl")


def load_jsonl(path: Path) -> List[Dict]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def manifest_for(samples: List[Dict], size: int, seed: int) -> Dict:
    supported = [sample for sample in samples if sample["supported"]]
    groups = defaultdict(list)
    for sample in supported:
        groups[sample["paired_group_id"]].append(sample)
    return {
        "dataset_name": "JianMu v0.7.0 Symbol Grounding Curriculum（符号接地课程）",
        "requested_size": size,
        "actual_total": len(samples),
        "seed": seed,
        "split_counts": dict(Counter(sample["split"] for sample in samples)),
        "curriculum_stage_counts": dict(Counter(sample["curriculum_stage"] for sample in samples)),
        "input_mode_counts": dict(Counter(sample["input_mode"] for sample in samples)),
        "paired_group_count": len(groups),
        "supported_count": len(supported),
        "unsupported_count": len(samples) - len(supported),
        "quality": {
            "duplicate_input_count": len(samples) - len({sample["input_text"] for sample in samples}),
            "paired_groups_with_arabic_and_zh": sum(1 for rows in groups.values() if {"arabic_math_expression", "zh_number_expression"} <= {row["input_mode"] for row in rows}),
        },
    }


def report_markdown(manifest: Dict, samples: List[Dict]) -> str:
    examples = _first_by(samples, "input_mode")
    lines = [
        "# v0.7.0 Symbol Grounding Curriculum（符号接地课程） Dataset Report",
        "",
        "This dataset provides teacher labels for Symbol Grounding（符号接地） while candidate generation only sees Raw Symbol Feature（原始符号特征） values.",
        "",
        "## Summary（摘要）",
        "",
        f"- total: {manifest['actual_total']}",
        f"- split counts: {manifest['split_counts']}",
        f"- curriculum_stage counts: {manifest['curriculum_stage_counts']}",
        f"- input_mode counts: {manifest['input_mode_counts']}",
        f"- paired_group count（成对复述组数量）: {manifest['paired_group_count']}",
        "",
        "## Examples（样例）",
        "",
    ]
    for mode, sample in examples.items():
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
            "- This is a Symbol Grounding Curriculum（符号接地课程） scaffold.",
        ]
    )
    return "\n".join(lines) + "\n"


def _split_counts(size: int) -> Dict[str, int]:
    if size < 120:
        raise ValueError("size must be at least 120")
    if size <= 800:
        train, eval_count, ood = int(size * 0.7), int(size * 0.2), size - int(size * 0.7) - int(size * 0.2)
    else:
        train, eval_count, ood = 2200, 600, size - 2800
    supported = train + eval_count
    return {
        "train": train,
        "eval": eval_count,
        "ood": ood,
        "numeral_grounding_samples": max(1, supported * 3 // 13),
        "operator_grounding_samples": max(1, supported * 5 // 13),
        "structure_grounding_samples": supported - (supported * 3 // 13) - (supported * 5 // 13),
    }


def _build_specs(rng: random.Random, count: int) -> List[GroundingSpec]:
    specs = []
    for index in range(count):
        stage = ["numeral_grounding", "operator_grounding", "structure_grounding"][index % 3]
        if stage == "numeral_grounding":
            value = rng.choice(list(range(-20, 51)))
            spec = _literal_spec(value, index)
        elif stage == "operator_grounding":
            a, b = rng.randint(1, 50), rng.randint(1, 50)
            op = rng.choice(["add", "sub", "mul", "div"])
            if op == "div":
                b = rng.choice([1, 2, 3, 4, 5, 6, 10])
                q = rng.randint(1, 8)
                a = b * q
            spec = _binary_spec(a, b, op, "operator_grounding", index)
        else:
            spec = _structure_spec(rng, index)
        specs.append(spec)
    return specs


def _literal_spec(value: int, index: int) -> GroundingSpec:
    return GroundingSpec(
        paired_group_id=f"sg_lit_{value}_{index}",
        curriculum_stage="numeral_grounding",
        canonical=f"lit({value})",
        expected_output=f"{value}\n",
        expression_family="literal_only",
        structure_policy="literal_value",
        symbol_slots=({"surface": _zh(value), "slot": "value", "target_literal": value},),
        operator_slots=(),
        arabic_expr=str(value),
        zh_expr=_zh(value),
        mixed_exprs=(f"输出{_zh(value)}", f"{_zh(value)}等于多少"),
    )


def _binary_spec(a: int, b: int, op: str, stage: str, index: int) -> GroundingSpec:
    names = {"add": ("+", "加", "addition", a + b), "sub": ("-", "减", "subtraction", a - b), "mul": ("*", "乘", "multiplication", a * b), "div": ("/", "除以", "exact_division", int(a / b))}
    ascii_op, zh_op, family, value = names[op]
    return GroundingSpec(
        paired_group_id=f"sg_{op}_{a}_{b}_{index}",
        curriculum_stage=stage,
        canonical=f"{op}(lit({a}),lit({b}))",
        expected_output=f"{value}\n",
        expression_family=family,
        structure_policy="binary_operation",
        symbol_slots=({"surface": _zh(a), "slot": "lhs", "target_literal": a}, {"surface": _zh(b), "slot": "rhs", "target_literal": b}),
        operator_slots=({"surface": zh_op, "target_operator": op},),
        arabic_expr=f"{a}{ascii_op}{b}",
        zh_expr=f"{_zh(a)}{zh_op}{_zh(b)}",
        mixed_exprs=(f"{_zh(a)}{zh_op}{b}", f"{a}{zh_op}{_zh(b)}"),
    )


def _structure_spec(rng: random.Random, index: int) -> GroundingSpec:
    a, b, c = rng.randint(1, 20), rng.randint(1, 20), rng.randint(1, 20)
    kind = rng.choice(["add_mul", "mul_add", "paren_add_mul", "neg_add", "div_add"])
    if kind == "add_mul":
        canonical, value, expr, zh, ops, family, structure = f"add(lit({a}),mul(lit({b}),lit({c})))", a + b * c, f"{a}+{b}*{c}", f"{_zh(a)}加{_zh(b)}乘{_zh(c)}", ({"surface": "加", "target_operator": "add"}, {"surface": "乘", "target_operator": "mul"}), "mixed_precedence", "precedence_tree"
    elif kind == "mul_add":
        canonical, value, expr, zh, ops, family, structure = f"add(mul(lit({a}),lit({b})),lit({c}))", a * b + c, f"{a}*{b}+{c}", f"{_zh(a)}乘{_zh(b)}加{_zh(c)}", ({"surface": "乘", "target_operator": "mul"}, {"surface": "加", "target_operator": "add"}), "mixed_precedence", "precedence_tree"
    elif kind == "paren_add_mul":
        canonical, value, expr, zh, ops, family, structure = f"mul(add(lit({a}),lit({b})),lit({c}))", (a + b) * c, f"({a}+{b})*{c}", f"括号里{_zh(a)}加{_zh(b)}再乘{_zh(c)}", ({"surface": "加", "target_operator": "add"}, {"surface": "乘", "target_operator": "mul"}), "parentheses", "parenthesized_tree"
    elif kind == "neg_add":
        a = -rng.randint(1, 20)
        canonical, value, expr, zh, ops, family, structure = f"add(lit({a}),lit({b}))", a + b, f"{a}+{b}", f"{_zh(a)}加{_zh(b)}", ({"surface": "加", "target_operator": "add"},), "addition", "binary_operation"
    else:
        b = rng.choice([1, 2, 3, 4, 6])
        q = rng.randint(2, 8)
        a = b * q
        canonical, value, expr, zh, ops, family, structure = f"add(div(lit({a}),lit({b})),lit({c}))", q + c, f"{a}/{b}+{c}", f"{_zh(a)}除以{_zh(b)}加{_zh(c)}", ({"surface": "除以", "target_operator": "div"}, {"surface": "加", "target_operator": "add"}), "mixed_precedence", "precedence_tree"
    symbols = tuple({"surface": _zh(n), "slot": f"n{i}", "target_literal": n} for i, n in enumerate(_numbers_from_canonical(canonical)))
    return GroundingSpec(f"sg_{kind}_{index}", "structure_grounding", canonical, f"{value}\n", family, structure, symbols, ops, expr, zh, (f"计算{zh}", f"输出{zh}"))


def _variants(spec: GroundingSpec) -> List[Tuple[str, str]]:
    return [
        (spec.arabic_expr, "arabic_math_expression"),
        (spec.zh_expr, "zh_number_expression"),
        (f"计算{spec.zh_expr}", "paired_zh_natural"),
        (spec.mixed_exprs[0], "mixed_zh_arabic"),
    ]


def _supported_sample(counter: int, split: str, spec: GroundingSpec, text: str, mode: str, seed: int) -> Dict:
    language = "math_expression_context" if mode in {"arabic_math_expression", "zh_number_expression"} else "implicit_C"
    return {
        "sample_id": f"jm-v070-{counter:06d}",
        "input_text": text,
        "split": split,
        "curriculum_stage": spec.curriculum_stage,
        "input_mode": mode,
        "paraphrase_group": spec.paired_group_id,
        "paired_group_id": spec.paired_group_id,
        "target_branch_path": [
            ["task_scope", "programming"],
            ["language_target", language],
            ["semantic_domain", "arithmetic"],
            ["arithmetic_family", spec.expression_family],
            ["structure_policy", spec.structure_policy],
            ["slot_binding_policy", "chinese_number_order" if mode != "arabic_math_expression" else "surface_number_order"],
            ["target_builder", "canonical_arithmetic_targetir"],
        ],
        "target_ir_canonical": spec.canonical,
        "expected_output": spec.expected_output,
        "supported": True,
        "unsupported_reason": None,
        "symbol_slots": list(spec.symbol_slots) if mode != "arabic_math_expression" else [],
        "operator_slots": list(spec.operator_slots),
        "expression_family": spec.expression_family,
        "structure_policy": spec.structure_policy,
        "source_generator": SOURCE_GENERATOR,
        "generator_seed": seed,
    }


def _ood_samples(start: int, count: int, seed: int, rng: random.Random) -> List[Dict]:
    rows = []
    for offset in range(count):
        if offset % 3 == 0:
            text, mode, reason, path = f"calculate {rng.randint(1, 20)} plus {rng.randint(1, 20)}", "ood_english", "unsupported_language", [["task_scope", "programming"], ["language_target", "reject_unsupported_language"]]
        elif offset % 3 == 1:
            text, mode, reason, path = f"写一首关于数字{rng.randint(1, 20)}的诗", "ood_unrelated", "unsupported_non_programming", [["task_scope", "reject_non_programming"]]
        else:
            text, mode, reason, path = f"输出 {rng.choice([5, 7, 11])}/{rng.choice([2, 3, 4])}", "unsupported_arithmetic", "division_not_exact", [["task_scope", "programming"], ["language_target", "math_expression_context"], ["semantic_domain", "arithmetic"], ["arithmetic_family", "unsupported"]]
        rows.append({
            "sample_id": f"jm-v070-{start + offset:06d}",
            "input_text": text,
            "split": "ood",
            "curriculum_stage": "ood",
            "input_mode": mode,
            "paraphrase_group": f"ood_{reason}_{offset}",
            "paired_group_id": f"ood_{reason}_{offset}",
            "target_branch_path": path,
            "target_ir_canonical": None,
            "expected_output": None,
            "supported": False,
            "unsupported_reason": reason,
            "symbol_slots": [],
            "operator_slots": [],
            "expression_family": None,
            "structure_policy": None,
            "source_generator": SOURCE_GENERATOR,
            "generator_seed": seed,
        })
    return rows


def _dedupe(samples: List[Dict]) -> List[Dict]:
    seen = set()
    result = []
    for sample in samples:
        if sample["input_text"] in seen:
            sample = dict(sample)
            sample["input_text"] = f"{sample['input_text']}（{sample['sample_id']}）"
        seen.add(sample["input_text"])
        result.append(sample)
    return result


def _write_jsonl(path: Path, samples: Iterable[Dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for sample in samples:
            handle.write(json.dumps(sample, ensure_ascii=False, sort_keys=True) + "\n")


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
    if value <= 50:
        tens, ones = divmod(value, 10)
        return digits[tens] + "十" + (digits[ones] if ones else "")
    return str(value)


def _numbers_from_canonical(canonical: str) -> List[int]:
    import re
    return [int(value) for value in re.findall(r"lit\((-?\d+)\)", canonical)]


def _first_by(samples: List[Dict], key: str) -> Dict[str, Dict]:
    result = {}
    for sample in samples:
        result.setdefault(sample[key], sample)
    return result


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Generate v0.7.0 Symbol Grounding Curriculum（符号接地课程） dataset.")
    parser.add_argument("--size", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--out", type=Path, default=Path("datasets/v0_7_0"))
    args = parser.parse_args(argv)
    manifest = write_symbol_grounding_dataset(args.size, args.seed, args.out)
    print(f"dataset total: {manifest['actual_total']}")
    print(f"split counts: {manifest['split_counts']}")
    print(f"curriculum_stage counts: {manifest['curriculum_stage_counts']}")
    print(f"report: {args.out / 'jianmu_v0_7_0_symbol_grounding_report.md'}")


if __name__ == "__main__":
    main()
