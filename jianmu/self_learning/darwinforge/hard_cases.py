import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class HardCase:
    input_text: str
    target_ir: Optional[str]
    expected_output: Optional[str]
    best_candidate_ir: Optional[str]
    best_fitness: float
    failure_reason: Optional[str]
    generation: int
    candidate_summary: Dict

    def to_dict(self) -> Dict:
        return {
            "input_text": self.input_text,
            "target_ir": self.target_ir,
            "expected_output": self.expected_output,
            "best_candidate_ir": self.best_candidate_ir,
            "best_fitness": self.best_fitness,
            "failure_reason": self.failure_reason,
            "generation": self.generation,
            "candidate_summary": dict(self.candidate_summary),
        }


class HardCaseBuffer:
    def __init__(self):
        self.items: List[HardCase] = []

    def add(self, record: HardCase):
        self.items.append(record)

    def sample(self, k: int, seed: int = 42) -> List[HardCase]:
        rng = random.Random(seed)
        if k >= len(self.items):
            return list(self.items)
        return rng.sample(self.items, k)

    def save_jsonl(self, path):
        Path(path).write_text(
            "".join(json.dumps(item.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for item in self.items),
            encoding="utf-8",
        )

    @classmethod
    def load_jsonl(cls, path):
        buffer = cls()
        p = Path(path)
        if not p.exists():
            return buffer
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            buffer.add(HardCase(**payload))
        return buffer

