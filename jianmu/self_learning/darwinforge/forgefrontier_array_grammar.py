from __future__ import annotations

from typing import Any, Dict


def fixed_array_spec(index: int = 0) -> Dict[str, Any]:
    return {"has_array": True, "has_pointer": False, "uses_dynamic_allocation": False, "array_length": 2 + index % 7, "array_index_static_safe": True}
