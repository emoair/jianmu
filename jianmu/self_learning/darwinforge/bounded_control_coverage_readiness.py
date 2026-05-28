from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def load_coverage_readiness(path: str | Path) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert "Turing completeness" not in payload.get("recommended_claim_level", "")
    return payload

