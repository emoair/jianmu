# SPDX-License-Identifier: AGPL-3.0-only

import hashlib
import json
import os

_MEMORY_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "route_memory.json")


def _situation_key(user_input: str, has_previous_ir: bool) -> str:
    """
    Normalize input to a coarse semantic situation key.
    Goal: similar intents (append one value, expand sum) should share the same key
    so that RouteMemory can transfer experience across paraphrases.
    Strategy: detect operation class (expand/append vs generate) + has_previous_ir.
    """
    import re
    text = user_input.strip().lower()
    # Detect operation class
    if re.search(r"多加|再加|扩展|改成|变成|加数", text):
        op_class = "expand"
    elif re.search(r"生成|定义|写一个", text):
        op_class = "generate"
    else:
        op_class = "other"
    payload = json.dumps({"op": op_class, "has_ir": has_previous_ir}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


class RouteMemory:
    def __init__(self, path: str = None):
        self._path = path or _MEMORY_FILE
        os.makedirs(os.path.dirname(self._path), exist_ok=True)

    def _load(self) -> dict:
        if not os.path.exists(self._path):
            return {}
        with open(self._path) as f:
            return json.load(f)

    def _save(self, data: dict):
        with open(self._path, "w") as f:
            json.dump(data, f, indent=2)

    def get_prior_boost(self, user_input: str, has_previous_ir: bool, route_id: str) -> float:
        """Return a prior score boost [0, 0.5] for a route based on past success."""
        key = _situation_key(user_input, has_previous_ir)
        data = self._load()
        entry = data.get(key, {}).get(route_id)
        if not entry:
            return 0.0
        total = entry["success_count"] + entry["failure_count"]
        if total == 0:
            return 0.0
        success_rate = entry["success_count"] / total
        return round(success_rate * 0.5, 3)  # max boost = 0.5

    def record(self, user_input: str, has_previous_ir: bool,
               route_id: str, success: bool, score: float):
        key = _situation_key(user_input, has_previous_ir)
        data = self._load()
        if key not in data:
            data[key] = {}
        if route_id not in data[key]:
            data[key][route_id] = {
                "route_id": route_id,
                "success_count": 0,
                "failure_count": 0,
                "avg_score": 0.0,
                "last_updated": "",
            }
        entry = data[key][route_id]
        if success:
            entry["success_count"] += 1
        else:
            entry["failure_count"] += 1
        total = entry["success_count"] + entry["failure_count"]
        entry["avg_score"] = round(
            (entry["avg_score"] * (total - 1) + score) / total, 4
        )
        import datetime
        entry["last_updated"] = datetime.datetime.utcnow().isoformat()
        self._save(data)

    def clear(self):
        self._save({})
