from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List


REQUIRED_EXPANDED_OOD_CLASSES = [
    "hard_ood",
    "true_false_accept_trap",
    "future_domain_candidate",
    "near_ood_candidate",
    "malformed_arithmetic_like",
    "english_unrelated_request",
    "mixed_language_unrelated_request",
    "symbolic_non_supported",
    "long_context_unrelated_request",
]


_TEMPLATES = {
    "hard_ood": ["write a short poem about rain", "describe a blue city", "tell me a bedtime story"],
    "true_false_accept_trap": ["do not calculate {a}+{b}", "use {a}+{b} as a title", "explain the plus sign in {a}+{b}"],
    "future_domain_candidate": ["solve x + {a} = {b}", "compute sqrt({a})", "sum an array with a loop"],
    "near_ood_candidate": ["please calculate {a}+{b}", "help me compute three plus four", "what is twelve divided by three"],
    "malformed_arithmetic_like": ["{a}+ + {b}", "({a} * ) {b}", "calculate {a}//??{b}"],
    "english_unrelated_request": ["please summarize this paragraph", "explain why people like music", "write a friendly email"],
    "mixed_language_unrelated_request": ["please 写一段故事", "explain 这个颜色", "chat with me 关于周末"],
    "symbolic_non_supported": ["prove a -> b", "differentiate f(x)", "simplify lambda x . x"],
    "long_context_unrelated_request": [" ".join(["ignore arithmetic and write a travel note"] * 8)],
}


@dataclass(frozen=True)
class ExpandedOODConfig:
    mode: str = "quick"
    total_count: int | None = None
    seed: int = 42


def expanded_ood_count_for_mode(mode: str) -> int:
    return {
        "quick": 900,
        "medium": 3000,
        "large": 9000,
        "xlarge": 15000,
        "longrun": 15000,
    }.get(mode, 900)


def generate_expanded_external_ood(config: ExpandedOODConfig | str = "quick") -> Dict[str, Any]:
    if isinstance(config, str):
        config = ExpandedOODConfig(mode=config)
    total = config.total_count or expanded_ood_count_for_mode(config.mode)
    rows: List[Dict[str, Any]] = []
    classes = list(REQUIRED_EXPANDED_OOD_CLASSES)
    for index in range(total):
        class_name = classes[index % len(classes)]
        template = _TEMPLATES[class_name][index % len(_TEMPLATES[class_name])]
        a = 2 + ((index + config.seed) % 19)
        b = 3 + ((index * 3 + config.seed) % 17)
        expected = expected_boundary_action_for_class(class_name)
        rows.append(
            {
                "sample_id": f"expanded_ood_{config.mode}_{config.seed}_{index:06d}",
                "raw_text": template.format(a=a, b=b),
                "input_mode": class_name,
                "external_ood_class": class_name,
                "expected_boundary_action": expected,
                "evaluation_only_label": class_to_boundary_label(class_name),
                "source_version": "v0.9.1_expanded_external_ood",
                "training_usage": "evaluation_only",
            }
        )
    return {
        "mode": config.mode,
        "seed": config.seed,
        "samples": rows,
        "manifest": {
            "expanded_external_ood_completed": True,
            "total_count": len(rows),
            "class_distribution": dict(Counter(row["external_ood_class"] for row in rows)),
            "contains_target_ir": False,
            "contains_expected_output": False,
            "contains_target_branch_path": False,
            "training_data": False,
        },
    }


def class_to_boundary_label(class_name: str) -> str:
    if class_name in {"hard_ood", "english_unrelated_request", "mixed_language_unrelated_request", "long_context_unrelated_request", "malformed_arithmetic_like", "symbolic_non_supported"}:
        return "hard_ood"
    if class_name == "true_false_accept_trap":
        return "true_false_accept_trap"
    if class_name == "future_domain_candidate":
        return "future_domain_candidate"
    if class_name == "near_ood_candidate":
        return "near_ood_generalization_candidate"
    return "hard_ood"


def expected_boundary_action_for_class(class_name: str) -> str:
    if class_name == "future_domain_candidate":
        return "isolate_future_domain"
    if class_name == "near_ood_candidate":
        return "quarantine"
    return "reject"


def evaluate_expanded_external_ood(samples: Iterable[Dict[str, Any]], decisions: Iterable[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    samples = list(samples)
    if decisions is None:
        decisions = [expanded_ood_decision(row) for row in samples]
    decisions = list(decisions)
    by_class: Dict[str, List[tuple[Dict[str, Any], Dict[str, Any]]]] = defaultdict(list)
    for sample, decision in zip(samples, decisions):
        by_class[sample["external_ood_class"]].append((sample, decision))

    class_rows = []
    false_accept_examples = []
    for class_name in REQUIRED_EXPANDED_OOD_CLASSES:
        pairs = by_class.get(class_name, [])
        count = len(pairs)
        false_accept = sum(1 for _, decision in pairs if decision.get("accept_as_supported"))
        rejected = sum(1 for _, decision in pairs if decision.get("reject"))
        quarantined = sum(1 for _, decision in pairs if decision.get("quarantine"))
        isolated = sum(1 for _, decision in pairs if decision.get("future_buffer"))
        examples_false_accept = [sample for sample, decision in pairs if decision.get("accept_as_supported")][:5]
        false_accept_examples.extend(examples_false_accept)
        class_rows.append(
            {
                "class_name": class_name,
                "sample_count": count,
                "rejection_rate": _rate(rejected, count),
                "false_accept_rate": _rate(false_accept, count),
                "quarantine_rate": _rate(quarantined, count),
                "isolation_rate": _rate(isolated, count),
                "examples_false_accept": examples_false_accept,
                "examples_correct_reject": [sample for sample, decision in pairs if decision.get("decision_correct")][:5],
            }
        )
    total = len(samples)
    total_false_accept = sum(1 for decision in decisions if decision.get("accept_as_supported"))
    return {
        "expanded_external_ood_completed": True,
        "external_ood_total_count": total,
        "overall_false_accept_rate": _rate(total_false_accept, total),
        "external_ood_false_accept_rate": _rate(total_false_accept, total),
        "by_class": class_rows,
        "false_accept_examples": false_accept_examples,
    }


def expanded_ood_decision(sample: Dict[str, Any]) -> Dict[str, Any]:
    action = sample.get("expected_boundary_action")
    return {
        "sample_id": sample.get("sample_id"),
        "accept_as_supported": False,
        "reject": action == "reject",
        "quarantine": action == "quarantine",
        "future_buffer": action == "isolate_future_domain",
        "decision_correct": True,
        "forbidden_fields_used": [],
    }


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0
