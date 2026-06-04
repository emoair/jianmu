from __future__ import annotations

from typing import List


def generate_chinese_paraphrases(nl_text: str) -> List[str]:
    return [
        nl_text,
        nl_text.replace("最后输出", "计算完成后输出"),
        nl_text.replace("声明变量", "先令变量"),
        "请根据以下过程求最终输出：" + nl_text,
    ]

