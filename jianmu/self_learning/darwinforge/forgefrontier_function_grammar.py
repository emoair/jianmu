from __future__ import annotations

from typing import Any, Dict


def pure_function_spec(index: int = 0) -> Dict[str, Any]:
    return {"has_function": True, "has_recursion": False, "has_pointer": False, "has_io": False, "max_call_depth": 2, "argument_count": 1 + index % 3}
