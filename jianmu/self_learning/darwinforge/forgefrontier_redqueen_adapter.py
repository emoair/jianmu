from __future__ import annotations

from typing import Any, Dict


def adapt_redqueen_to_frontier() -> Dict[str, Any]:
    return {"redqueen_enabled": True, "frontier_focus": ["function_boundary", "array_boundary"], "architecture_change": False}
