from __future__ import annotations

from typing import Any, Dict


def adapt_hydrabudget_to_frontier() -> Dict[str, Any]:
    return {"hydrabudget_enabled": True, "shadow_budget_only": True, "architecture_change": False}
