from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class OODToxicityClass:
    class_id: str
    class_name: str
    chinese_name: str
    detection_features: List[str]
    expected_rejection_layers: List[str]
    toxic_if_accepted: bool = True
    positive_if_rejected: bool = True

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


OOD_CLASSES = {
    "ood_english_sentence": OODToxicityClass("ood_english_sentence", "OOD English Sentence", "英文句子分布外", ["has_english_sentence"], ["language_target", "support_gate"]),
    "ood_unrelated_request": OODToxicityClass("ood_unrelated_request", "OOD Unrelated Request", "无关请求", ["unrelated_keyword_signal"], ["task_scope", "support_gate"]),
    "unsupported_arithmetic": OODToxicityClass("unsupported_arithmetic", "Unsupported Arithmetic", "不支持算术", ["unsupported_arithmetic_signal"], ["arithmetic_family", "structure_policy", "support_gate"]),
    "non_exact_division": OODToxicityClass("non_exact_division", "Non-Exact Division", "非整除", ["non_exact_division_signal"], ["arithmetic_family", "support_gate"]),
    "division_by_zero": OODToxicityClass("division_by_zero", "Division By Zero", "除零", ["division_by_zero_signal"], ["arithmetic_family", "support_gate"]),
    "unsupported_depth": OODToxicityClass("unsupported_depth", "Unsupported Depth", "超深表达式", ["unsupported_depth_signal"], ["structure_policy", "support_gate"]),
    "unsupported_operator": OODToxicityClass("unsupported_operator", "Unsupported Operator", "不支持运算符", ["unsupported_operator_signal"], ["arithmetic_family", "structure_policy"]),
    "mixed_language_query": OODToxicityClass("mixed_language_query", "Mixed Language Query", "混合语言查询", ["mixed_language_signal"], ["language_target", "support_gate"]),
    "instruction_not_programming": OODToxicityClass("instruction_not_programming", "Instruction Not Programming", "非编程指令", ["unrelated_keyword_signal"], ["task_scope"]),
    "malformed_expression": OODToxicityClass("malformed_expression", "Malformed Expression", "畸形表达式", ["malformed_expression_signal"], ["structure_policy", "target_builder"]),
}


def classify_ood_sample(sample: Dict, features: Dict = None) -> OODToxicityClass:
    features = features or {}
    mode = sample.get("input_mode", "")
    reason = sample.get("unsupported_reason", "")
    text = sample.get("input_text", "")
    if mode == "ood_english":
        return OOD_CLASSES["ood_english_sentence"]
    if mode == "ood_unrelated":
        return OOD_CLASSES["ood_unrelated_request"]
    if reason == "division_by_zero" or "/0" in text:
        return OOD_CLASSES["division_by_zero"]
    if reason == "non_exact_division":
        return OOD_CLASSES["non_exact_division"]
    if reason == "unsupported_depth":
        return OOD_CLASSES["unsupported_depth"]
    if reason == "unsupported_operator" or "^" in text or "%" in text:
        return OOD_CLASSES["unsupported_operator"]
    if features.get("mixed_language_signal") or ("please" in text.lower() and any("\u4e00" <= ch <= "\u9fff" for ch in text)):
        return OOD_CLASSES["mixed_language_query"]
    if mode == "unsupported_arithmetic":
        return OOD_CLASSES["unsupported_arithmetic"]
    if sample.get("task_family") == "instruction_not_programming":
        return OOD_CLASSES["instruction_not_programming"]
    if features.get("malformed_expression_signal") or text.count("(") != text.count(")"):
        return OOD_CLASSES["malformed_expression"]
    return OOD_CLASSES["ood_unrelated_request"]


def summarize_ood_taxonomy(records: Iterable[Dict]) -> Dict:
    rows = list(records)
    distribution = Counter(row.get("ood_class") for row in rows)
    false_accept = Counter(row.get("ood_class") for row in rows if row.get("accepted_as_supported"))
    correct_reject = Counter(row.get("ood_class") for row in rows if not row.get("accepted_as_supported"))
    toxic = Counter(row.get("ood_class") for row in rows if row.get("toxic_nutrient", 0) > 0)
    layer = defaultdict(Counter)
    for row in rows:
        layer[row.get("ood_class")][row.get("rejection_layer", "unknown")] += 1
    return {
        "ood_class_distribution": dict(distribution),
        "ood_false_accept_by_class": dict(false_accept),
        "ood_correct_rejection_by_class": dict(correct_reject),
        "toxic_event_by_class": dict(toxic),
        "rejection_layer_by_class": {name: dict(counter) for name, counter in layer.items()},
    }
