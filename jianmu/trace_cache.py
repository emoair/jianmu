import hashlib
import json
import os

_CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "trace_cache.json")


def _cache_key(intent: dict, prev_ir_dict: dict = None) -> str:
    payload = json.dumps({"intent": intent, "prev_ir": prev_ir_dict}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


class TraceCache:
    def __init__(self, path: str = None):
        self._path = path or _CACHE_FILE
        os.makedirs(os.path.dirname(self._path), exist_ok=True)

    def _load(self) -> dict:
        if not os.path.exists(self._path):
            return {}
        with open(self._path) as f:
            return json.load(f)

    def _save(self, data: dict):
        with open(self._path, "w") as f:
            json.dump(data, f, indent=2)

    def get(self, intent: dict, prev_ir_dict: dict = None):
        return self._load().get(_cache_key(intent, prev_ir_dict))

    def put(self, intent: dict, prev_ir_dict: dict, record: dict):
        data = self._load()
        data[_cache_key(intent, prev_ir_dict)] = record
        self._save(data)

    def clear(self):
        self._save({})
