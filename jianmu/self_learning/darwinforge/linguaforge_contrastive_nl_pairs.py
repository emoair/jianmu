from __future__ import annotations

from typing import List, Tuple


def build_contrastive_pairs() -> List[Tuple[str, str]]:
    return [
        ("循环固定3次，每次加1。", "循环没有明确次数，一直加1。"),
        ("如果x大于2则加1，否则减1。", "如果x不大于2则加1，否则减1。"),
        ("读取数组第0位。", "读取数组第10位。"),
    ]

