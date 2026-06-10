from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


POLICY_SAMPLE_TARGETS = {
    "canonical_arithmetic_targetir": 40,
    "canonical_function_targetir": 60,
    "canonical_array_targetir": 60,
    "canonical_function_array_targetir": 60,
    "canonical_structured_recursion_targetir": 40,
    "mixed_extended_ir_path": 40,
}


@dataclass(frozen=True)
class HumanReviewPackConfig:
    total_review_samples: int = 300
    arithmetic_samples: int = 40
    function_samples: int = 60
    array_samples: int = 60
    function_array_samples: int = 60
    structured_recursion_samples: int = 40
    mixed_extended_ir_samples: int = 40
    replay_validation_samples: int = 1000
    replay_minimum_required: int = 300
    replay_must_include_all_policies: bool = True
    workers: int = 16
    compiler_workers: int = 16
    trace_writer_mode: str = "sharded"
    temp_dir_mode: str = "per_sample"
    accounting_lock: bool = True
    seed: int = 197

    def policy_targets(self) -> Dict[str, int]:
        return dict(POLICY_SAMPLE_TARGETS)

    def to_dict(self) -> Dict[str, object]:
        return {
            "total_review_samples": self.total_review_samples,
            "replay_validation_samples": self.replay_validation_samples,
            "replay_minimum_required": self.replay_minimum_required,
            "replay_must_include_all_policies": self.replay_must_include_all_policies,
            "workers": self.workers,
            "compiler_workers": self.compiler_workers,
            "trace_writer_mode": self.trace_writer_mode,
            "temp_dir_mode": self.temp_dir_mode,
            "accounting_lock": self.accounting_lock,
            "seed": self.seed,
            "policy_targets": self.policy_targets(),
        }


STILL_NOT_PROVEN = [
    "production function support",
    "production array support",
    "production recursion support",
    "arbitrary project parsing",
    "formal Turing completeness proof",
    "solved program synthesis",
    "production readiness",
    "natural language layer completed",
    "safe real promotion",
    "stable convergence",
    "solved OOD",
    "emergence proven",
]

