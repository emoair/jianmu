from __future__ import annotations

from typing import Any, Dict, List


def schedule_redqueen_specs(failure_mining: Dict[str, Any]) -> List[Dict[str, Any]]:
    specs = list(failure_mining.get("data_need_specs", []))
    return sorted(specs, key=lambda item: (-int(item["difficulty"]), str(item["target_stage"])))

