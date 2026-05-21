from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.lifecycle_memory_capture import capture_lifecycle_runtime_state
from jianmu.self_learning.darwinforge.nutrient_toxic_memory_capture import capture_nutrient_toxic_runtime_memory
from jianmu.self_learning.darwinforge.trained_branch_population_capture import capture_trained_branch_population
from jianmu.self_learning.darwinforge.trained_root_colony_capture import capture_trained_root_colonies


@dataclass(frozen=True)
class RuntimeStateCaptureConfig:
    enabled: bool = True
    capture_branch_population: bool = True
    capture_root_colonies: bool = True
    capture_lifecycle_states: bool = True
    capture_nutrient_toxic_memory: bool = True
    capture_curriculum_deltas: bool = True
    capture_every_stage: bool = True
    capture_every_n_steps: int | None = None
    output_dir: str = "records/v0_9_0/state"


class RuntimeStateCapture:
    def __init__(self, config: RuntimeStateCaptureConfig):
        self.config = config
        self.events: List[Dict[str, Any]] = []
        self.training_config: Dict[str, Any] = {}
        self.branch_population_state: Dict[str, Any] | None = None
        self.root_colony_state: Dict[str, Any] | None = None
        self.lifecycle_state: Dict[str, Any] | None = None
        self.nutrient_toxic_memory: Dict[str, Any] | None = None
        self.curriculum_deltas: List[Dict[str, Any]] = []
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)

    def on_training_start(self, config: Dict[str, Any]) -> None:
        self.training_config = dict(config)
        self._event("training_start", {"config_keys": sorted(config)})

    def on_branch_population_update(self, branch_population: Any) -> None:
        if not self.config.enabled or not self.config.capture_branch_population:
            return
        state = capture_trained_branch_population(
            branch_population,
            generation_count=getattr(branch_population, "generation", 0),
            seed=getattr(branch_population, "seed", self.training_config.get("seed", 42)),
        )
        self.branch_population_state = state.to_dict()
        self._event("branch_population_update", {"neuron_count": len(self.branch_population_state["branch_neuron_states"])})

    def on_root_colony_update(
        self,
        root_colonies: List[Any],
        quarantine_buffer: List[Dict[str, Any]] | None = None,
        future_domain_buffer: List[Dict[str, Any]] | None = None,
        near_ood_candidate_buffer: List[Dict[str, Any]] | None = None,
    ) -> None:
        if not self.config.enabled or not self.config.capture_root_colonies:
            return
        state = capture_trained_root_colonies(
            root_colonies,
            quarantine_buffer=quarantine_buffer,
            future_domain_buffer=future_domain_buffer,
            near_ood_candidate_buffer=near_ood_candidate_buffer,
            seed=self.training_config.get("seed", 42),
        )
        self.root_colony_state = state.to_dict()
        self._event("root_colony_update", {"colony_count": state.colony_count, "root_count": state.root_count})

    def on_lifecycle_update(self, lifecycle_state: Dict[str, Any]) -> None:
        if not self.config.enabled or not self.config.capture_lifecycle_states:
            return
        self.lifecycle_state = dict(lifecycle_state)
        self._event("lifecycle_update", {"event_count": len(self.lifecycle_state)})

    def on_nutrient_toxic_memory_update(self, memory_state: Dict[str, Any]) -> None:
        if not self.config.enabled or not self.config.capture_nutrient_toxic_memory:
            return
        self.nutrient_toxic_memory = dict(memory_state)
        self._event("nutrient_toxic_memory_update", {"event_count": len(self.nutrient_toxic_memory)})

    def on_curriculum_stage_end(self, stage_name: str, state_snapshot: Dict[str, Any]) -> None:
        if not self.config.enabled or not self.config.capture_curriculum_deltas:
            return
        self.curriculum_deltas.append({"stage_name": stage_name, "state_snapshot": dict(state_snapshot)})
        self._event("curriculum_stage_end", {"stage_name": stage_name})

    def on_training_end(self, final_state: Dict[str, Any]) -> None:
        self._event("training_end", {"final_state_keys": sorted(final_state)})

    def capture_from_training_result(self, training_result: Dict[str, Any]) -> None:
        if self.root_colony_state and self.config.capture_lifecycle_states:
            lifecycle = capture_lifecycle_runtime_state(training_result, self.root_colony_state)
            self.on_lifecycle_update(lifecycle.to_dict())
        if self.config.capture_nutrient_toxic_memory:
            memory = capture_nutrient_toxic_runtime_memory(training_result)
            self.on_nutrient_toxic_memory_update(memory.to_dict())
        for row in training_result.get("stage_metrics", []):
            self.on_curriculum_stage_end(row.get("stage_name", "unknown"), row)

    def export_full_runtime_state(self) -> Dict[str, Any]:
        missing = []
        if self.config.capture_branch_population and not self.branch_population_state:
            missing.append("trained_branch_population")
        if self.config.capture_root_colonies and not self.root_colony_state:
            missing.append("trained_root_colonies")
        if self.config.capture_lifecycle_states and not self.lifecycle_state:
            missing.append("lifecycle_runtime_states")
        if self.config.capture_nutrient_toxic_memory and not self.nutrient_toxic_memory:
            missing.append("nutrient_toxic_runtime_memory")
        return {
            "capture_config": asdict(self.config),
            "capture_enabled": self.config.enabled,
            "branch_population_captured": self.branch_population_state is not None,
            "root_colonies_captured": self.root_colony_state is not None,
            "lifecycle_states_captured": self.lifecycle_state is not None,
            "nutrient_toxic_memory_captured": self.nutrient_toxic_memory is not None,
            "curriculum_deltas_captured": bool(self.curriculum_deltas),
            "capture_event_count": len(self.events),
            "missing_capture_components": missing,
            "runtime_capture_passed": self.config.enabled and not missing,
            "events": list(self.events),
            "training_config": dict(self.training_config),
            "trained_branch_population": self.branch_population_state,
            "trained_root_colonies": self.root_colony_state,
            "lifecycle_runtime_states": self.lifecycle_state,
            "nutrient_toxic_runtime_memory": self.nutrient_toxic_memory,
            "curriculum_stage_deltas": list(self.curriculum_deltas),
        }

    def _event(self, event_type: str, payload: Dict[str, Any]) -> None:
        self.events.append({"event_index": len(self.events), "event_type": event_type, "payload": payload})


def build_lifecycle_memory_from_training(training_result: Dict[str, Any], root_colony_state: Dict[str, Any]) -> Dict[str, Any]:
    return capture_lifecycle_runtime_state(training_result, root_colony_state).to_dict()


def build_nutrient_toxic_memory_from_training(training_result: Dict[str, Any]) -> Dict[str, Any]:
    return capture_nutrient_toxic_runtime_memory(training_result).to_dict()
