from dataclasses import dataclass
from typing import List

from jianmu.self_learning.ir_tokens import IRToken, expected_binary_add_tokens


@dataclass(frozen=True)
class PrefixTrainingTask:
    task_id: str
    input_text: str
    target_tokens: List[IRToken]
    expected_output: str


def build_tiny_prefix_dataset() -> List[PrefixTrainingTask]:
    examples = [
        ("task_001", "写一个 C 程序输出 1+2", 1, 2),
        ("task_002", "写一个 C 程序输出 2+3", 2, 3),
        ("task_003", "写一个 C 程序输出 3+4", 3, 4),
        ("task_004", "写一个 C 程序输出 一+二", 1, 2),
        ("task_005", "写一个 C 程序输出 二+三", 2, 3),
        ("task_006", "用 printf 输出 4+5", 4, 5),
    ]
    return [
        PrefixTrainingTask(
            task_id=task_id,
            input_text=input_text,
            target_tokens=expected_binary_add_tokens(left, right),
            expected_output=f"{left + right}\n",
        )
        for task_id, input_text, left, right in examples
    ]

