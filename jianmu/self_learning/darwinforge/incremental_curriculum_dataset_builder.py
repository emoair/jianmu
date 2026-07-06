from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.incremental_dataset_schema import IncrementalDatasetConfig
from jianmu.self_learning.darwinforge.streaming_dataset_writer import write_streaming_dataset


def build_incremental_curriculum_dataset(output_records: str | Path, dataset_artifact_root: str | Path, config: IncrementalDatasetConfig, redqueen_schedule: dict, mirror_feedback: dict) -> dict:
    return write_streaming_dataset(Path(output_records), Path(dataset_artifact_root), config, redqueen_schedule, mirror_feedback)
