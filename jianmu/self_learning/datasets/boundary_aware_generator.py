from __future__ import annotations

import random
from typing import Dict, List

from jianmu.self_learning.datasets.boundary_labels import BoundaryLabel, ExpectedAction, NutrientPolicy, make_boundary_sample
from jianmu.self_learning.datasets.nutrient_policy_labels import attach_nutrient_policy


ZH_NUM = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]


def generate_boundary_aware_samples(total: int, seed: int = 42, source_candidates: List[Dict] | None = None) -> List[Dict]:
    rng = random.Random(seed)
    counts = _target_counts(total)
    samples: List[Dict] = []
    index = 0
    for label, count in counts.items():
        for _ in range(count):
            index += 1
            samples.append(_make_sample(label, index, rng, source_candidates or []))
    rng.shuffle(samples)
    for i, sample in enumerate(samples):
        sample["sample_id"] = f"jm-v085-{i:07d}"
    return samples


def _target_counts(total: int) -> Dict[str, int]:
    ratios = [
        (BoundaryLabel.CURRENT_SUPPORTED.value, 0.45),
        (BoundaryLabel.HARD_OOD.value, 0.15),
        (BoundaryLabel.TRUE_FALSE_ACCEPT_TRAP.value, 0.15),
        (BoundaryLabel.FUTURE_DOMAIN_CANDIDATE.value, 0.15),
        (BoundaryLabel.NEAR_OOD_GENERALIZATION_CANDIDATE.value, 0.08),
        (BoundaryLabel.LABEL_REVIEW_CANDIDATE.value, 0.02),
    ]
    counts = {label: int(total * ratio) for label, ratio in ratios}
    counts[BoundaryLabel.CURRENT_SUPPORTED.value] += total - sum(counts.values())
    return counts


def _make_sample(label: str, index: int, rng: random.Random, source_candidates: List[Dict]) -> Dict:
    if label == BoundaryLabel.CURRENT_SUPPORTED.value:
        row = _current_supported(index, rng)
    elif label == BoundaryLabel.HARD_OOD.value:
        row = _hard_ood(index, rng)
    elif label == BoundaryLabel.TRUE_FALSE_ACCEPT_TRAP.value:
        row = _trap(index, rng)
    elif label == BoundaryLabel.FUTURE_DOMAIN_CANDIDATE.value:
        row = _future(index, rng, source_candidates)
    elif label == BoundaryLabel.NEAR_OOD_GENERALIZATION_CANDIDATE.value:
        row = _near(index, rng)
    else:
        row = _review(index, rng)
    return attach_nutrient_policy(row)


def _current_supported(index: int, rng: random.Random) -> Dict:
    a = rng.randint(-50, 99)
    b = rng.randint(1, 99)
    op = rng.choice(["+", "-", "*", "/"])
    if op == "/":
        b = rng.randint(1, 12)
        q = rng.randint(-20, 20)
        a = b * q
    value = _eval(a, b, op)
    canonical = f"{a}{op}{b}"
    raw_templates = [
        f"计算{a}{op}{b}",
        f"输出 {canonical}",
        f"请计算 {canonical} 的结果",
        f"{canonical}",
        f"计算{_zh(a)}{_op_zh(op)}{_zh(b)}",
    ]
    raw = raw_templates[index % len(raw_templates)]
    return make_boundary_sample(
        sample_id=f"tmp-{index}",
        raw_text=raw,
        canonical_text=canonical,
        input_mode="current_supported_arithmetic",
        boundary_label=BoundaryLabel.CURRENT_SUPPORTED,
        expected_action=ExpectedAction.ACCEPT_AND_SYNTHESIZE,
        nutrient_policy=[NutrientPolicy.POSITIVE_ON_CORRECT_ACCEPT],
        toxicity_policy=[NutrientPolicy.TOXIC_ON_FALSE_REJECT],
        current_support_status="supported",
        future_support_status="supported_now",
        target_ir=_target_ir(a, b, op),
        expected_output=f"{value}\n",
        source_version="v0.8.5",
        source_reason="generated_current_supported",
        paraphrase_group_id=f"pg-current-{a}-{op}-{b}",
        target_group_id=f"tg-{canonical}",
    )


def _hard_ood(index: int, rng: random.Random) -> Dict:
    templates = [
        "写一首关于数字{n}的诗",
        "画一张关于{n}的图片",
        "今天天气怎么样",
        "启动一个 HTTP server",
        "随便聊聊宇宙",
        "生成一段无关文本 {n}",
    ]
    n = rng.randint(1, 99)
    raw = templates[index % len(templates)].format(n=n)
    return make_boundary_sample(
        sample_id=f"tmp-{index}",
        raw_text=raw,
        canonical_text=raw,
        input_mode="hard_ood",
        boundary_label=BoundaryLabel.HARD_OOD,
        expected_action=ExpectedAction.REJECT,
        nutrient_policy=[NutrientPolicy.POSITIVE_ON_CORRECT_REJECT],
        toxicity_policy=[NutrientPolicy.TOXIC_ON_FALSE_ACCEPT],
        current_support_status="unsupported_now",
        future_support_status="not_planned",
        ood_class="hard_ood",
        source_version="v0.8.5",
        source_reason="generated_hard_ood",
    )


def _trap(index: int, rng: random.Random) -> Dict:
    a, b = rng.randint(1, 50), rng.randint(1, 50)
    expr = f"{a}+{b}"
    templates = [
        f"写一个关于{expr}的故事",
        f"用{expr}写首诗",
        f"解释为什么 {expr} 很浪漫",
        f"把 {expr} 作为标题",
        f"不要计算 {expr}",
        f"分别说明 {a} 和 {b}，不要求求和",
        f"输出文字“{expr}”而不是结果",
    ]
    raw = templates[index % len(templates)]
    return make_boundary_sample(
        sample_id=f"tmp-{index}",
        raw_text=raw,
        canonical_text=raw,
        input_mode="true_false_accept_trap",
        boundary_label=BoundaryLabel.TRUE_FALSE_ACCEPT_TRAP,
        expected_action=ExpectedAction.REJECT,
        nutrient_policy=[NutrientPolicy.POSITIVE_ON_CORRECT_REJECT],
        toxicity_policy=[NutrientPolicy.TOXIC_ON_FALSE_ACCEPT],
        current_support_status="unsupported_now",
        future_support_status="not_planned",
        ood_class="true_false_accept_trap",
        source_version="v0.8.5",
        source_reason="generated_true_false_accept_trap",
    )


def _future(index: int, rng: random.Random, source_candidates: List[Dict]) -> Dict:
    if source_candidates:
        candidate = source_candidates[index % len(source_candidates)]
        raw = candidate.get("raw_text") or "future domain candidate"
        canonical = candidate.get("canonical_text") or raw
        reason = f"seeded_from_{candidate.get('source_version', 'v0_8_4')}"
    else:
        a, b = rng.randint(1, 99), rng.randint(2, 99)
        templates = [f"calculate {a} plus {b}", f"输出 {a}/{b}", f"求 x+{a}={b}", f"计算 {a}.5+{b}.2", f"写一个数组循环求和程序"]
        raw = templates[index % len(templates)]
        canonical = raw
        reason = "generated_future_domain"
    return make_boundary_sample(
        sample_id=f"tmp-{index}",
        raw_text=raw,
        canonical_text=canonical,
        input_mode="future_domain_candidate",
        boundary_label=BoundaryLabel.FUTURE_DOMAIN_CANDIDATE,
        expected_action=ExpectedAction.REJECT_BUT_KEEP_FUTURE_CANDIDATE,
        nutrient_policy=[NutrientPolicy.WEAK_POSITIVE_ON_CURRENT_REJECT],
        toxicity_policy=[NutrientPolicy.NEUTRAL_ON_CURRENT_REJECT],
        current_support_status="unsupported_now",
        future_support_status="future_candidate",
        ood_class="future_domain_candidate",
        source_version="v0.8.5",
        source_reason=reason,
    )


def _near(index: int, rng: random.Random) -> Dict:
    a, b = rng.randint(1, 50), rng.randint(1, 50)
    raw = [f"帮我算一下{_zh(a)}加{_zh(b)}", f"麻烦输出{a}+{b}的结果", f"请给出 {a}+{b} 的答案", f"算算看{_zh(a)}乘{_zh(b)}"][index % 4]
    canonical = f"{a}+{b}" if index % 4 != 3 else f"{a}*{b}"
    return make_boundary_sample(
        sample_id=f"tmp-{index}",
        raw_text=raw,
        canonical_text=canonical,
        input_mode="near_ood_generalization_candidate",
        boundary_label=BoundaryLabel.NEAR_OOD_GENERALIZATION_CANDIDATE,
        expected_action=ExpectedAction.CANDIDATE_BUFFER_ONLY,
        nutrient_policy=[NutrientPolicy.NEUTRAL_ON_CURRENT_REJECT],
        toxicity_policy=[NutrientPolicy.NEUTRAL_ON_CURRENT_REJECT],
        current_support_status="not_training_supported",
        future_support_status="review_for_supported_expansion",
        ood_class="near_ood_generalization_candidate",
        source_version="v0.8.5",
        source_reason="generated_near_ood_candidate",
        paraphrase_group_id=f"pg-near-{a}-{b}-{index % 4}",
        target_group_id=f"tg-near-{canonical}",
    )


def _review(index: int, rng: random.Random) -> Dict:
    raw = [f"说明数字 {rng.randint(1, 99)} 的含义", "输出三加四这几个字", "给我一个数学相关标题"][index % 3]
    return make_boundary_sample(
        sample_id=f"tmp-{index}",
        raw_text=raw,
        canonical_text=raw,
        input_mode="label_review_candidate",
        boundary_label=BoundaryLabel.LABEL_REVIEW_CANDIDATE,
        expected_action=ExpectedAction.QUARANTINE_FOR_REVIEW,
        nutrient_policy=[NutrientPolicy.NO_TRAINING_SIGNAL_REVIEW_ONLY],
        toxicity_policy=[NutrientPolicy.NO_TRAINING_SIGNAL_REVIEW_ONLY],
        current_support_status="review_only",
        future_support_status="review_only",
        ood_class="label_review_candidate",
        source_version="v0.8.5",
        source_reason="generated_label_review",
    )


def _eval(a: int, b: int, op: str) -> int:
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    return int(a / b)


def _target_ir(a: int, b: int, op: str) -> str:
    name = {"+": "add", "-": "sub", "*": "mul", "/": "div"}[op]
    return f"{name}(lit({a}),lit({b}))"


def _zh(n: int) -> str:
    if n < 0:
        return "负" + _zh(-n)
    if n <= 10:
        return ZH_NUM[n]
    return str(n)


def _op_zh(op: str) -> str:
    return {"+": "加", "-": "减", "*": "乘以", "/": "除以"}[op]
