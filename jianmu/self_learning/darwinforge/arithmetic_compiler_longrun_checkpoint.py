from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict


def write_longrun_checkpoint(path: str | Path, payload: Dict[str, Any]) -> None:
    checkpoint = {
        "timestamp": time.time(),
        **payload,
    }
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(checkpoint, ensure_ascii=False, sort_keys=True) + "\n")
