from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable


def analyze_bandit_stability(policy: Dict[str, Any], output_records: str | Path | None = None) -> Dict[str, Any]:
    history = policy.get("arm_selection_history", [])
    selected = [row.get("selected_arm") or row.get("arm_id") for row in history if row.get("selected_arm") or row.get("arm_id")]
    counts = Counter(selected)
    total = max(sum(counts.values()), 1)
    entropy = -sum((count / total) * math.log(count / total, 2) for count in counts.values())
    max_share = max((count / total for count in counts.values()), default=0.0)
    contrastive = sum(count for arm, count in counts.items() if "contrast" in arm) / total
    high_roi = sum(count for arm, count in counts.items() if arm in set(policy.get("promoted_arms", []))) / total
    rewards = [float(row.get("reward", 0.0)) for row in policy.get("reward_trace", [])]
    mean = sum(rewards) / max(len(rewards), 1)
    variance = sum((value - mean) ** 2 for value in rewards) / max(len(rewards), 1)
    result = {
        "arm_selection_entropy": round(entropy, 6),
        "promoted_arms": policy.get("promoted_arms", []),
        "retired_arms": policy.get("retired_arms", []),
        "arm_collapse_detected": max_share > 0.60,
        "overselected_arm_count": sum(1 for count in counts.values() if count / total > 0.35),
        "exploration_rate_final": policy.get("epsilon_min", 0.05),
        "exploitation_rate": round(1.0 - float(policy.get("epsilon_min", 0.05)), 6),
        "high_roi_arm_selection_rate": round(high_roi, 6),
        "contrastive_arm_selection_rate": round(contrastive, 6),
        "reward_variance": round(variance, 6),
        "reward_stability_score": round(max(0.0, 1.0 - variance), 6),
        "scheduler_stable": max_share <= 0.60 and variance < 0.25,
    }
    if output_records is not None:
        out = Path(output_records)
        _write_json(out / "bandit_stability_analysis.json", result)
        (out / "bandit_stability_analysis.md").write_text("\n".join(["# Bandit Stability", "", *(f"- {k}: {v}" for k, v in result.items())]) + "\n", encoding="utf-8")
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
