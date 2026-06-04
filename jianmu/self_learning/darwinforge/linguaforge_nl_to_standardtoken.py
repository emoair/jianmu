from __future__ import annotations

from typing import Any, Dict

from jianmu.self_learning.darwinforge.linguaforge_nl_schema import nl_to_standardtoken


def map_nl_to_standardtoken(nl_text: str, category: str | None = None, sample_index: int = 0) -> Dict[str, Any]:
    return nl_to_standardtoken(nl_text, category=category, sample_index=sample_index)

