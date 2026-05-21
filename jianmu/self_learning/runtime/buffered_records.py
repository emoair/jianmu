from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class BufferedRecordConfig:
    buffer_size: int = 5000
    checkpoint_interval_sec: int = 600
    runtime_tmp_dir: str = "runtime-cache"
    final_records_dir: str = "records/v0_8_2"
    flush_on_close: bool = True
    write_worker_shards: bool = True
    merge_after_run: bool = True


class BufferedRecordWriter:
    def __init__(self, run_id: str, worker_id: int, config: BufferedRecordConfig):
        self.run_id = run_id
        self.worker_id = worker_id
        self.config = config
        self.runtime_tmp_dir = Path(config.runtime_tmp_dir)
        self.final_records_dir = Path(config.final_records_dir)
        self.shard_dir = self.runtime_tmp_dir / "shards"
        self.checkpoint_dir = self.runtime_tmp_dir / "checkpoints"
        self.shard_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.final_records_dir.mkdir(parents=True, exist_ok=True)
        self.buffer: List[Dict[str, Any]] = []
        self.last_checkpoint = time.time()
        self.buffered_record_count = 0
        self.flush_count = 0
        self.checkpoint_count = 0
        self.partial_checkpoint_count = 0
        self.record_write_time_seconds = 0.0

    @property
    def shard_path(self) -> Path:
        return self.shard_dir / f"worker_{self.worker_id}.jsonl"

    def append(self, record: Dict[str, Any]) -> None:
        row = {
            "run_id": self.run_id,
            "worker_id": self.worker_id,
            "timestamp": round(time.time(), 6),
            "record_type": record.get("record_type", "generic"),
            **record,
        }
        self.buffer.append(row)
        self.buffered_record_count += 1
        if len(self.buffer) >= self.config.buffer_size:
            self.flush()
        if time.time() - self.last_checkpoint >= self.config.checkpoint_interval_sec:
            self.checkpoint()

    def flush(self) -> None:
        if not self.buffer:
            return
        started = time.time()
        with self.shard_path.open("a", encoding="utf-8", newline="\n") as handle:
            for row in self.buffer:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        self.buffer.clear()
        self.flush_count += 1
        self.record_write_time_seconds += time.time() - started

    def checkpoint(self) -> Path:
        self.flush()
        self.last_checkpoint = time.time()
        self.checkpoint_count += 1
        path = self.checkpoint_dir / f"worker_{self.worker_id}_checkpoint_{self.checkpoint_count}.jsonl"
        if self.shard_path.exists():
            path.write_text(self.shard_path.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            path.write_text("", encoding="utf-8")
        self.partial_checkpoint_count += 1
        return path

    def close(self) -> Dict[str, Any]:
        if self.config.flush_on_close:
            self.flush()
        return self.summary()

    def merge_worker_shards(self, output_name: str = "merged_records.jsonl") -> Dict[str, Any]:
        started = time.time()
        output = self.final_records_dir / output_name
        with output.open("w", encoding="utf-8", newline="\n") as out:
            for path in sorted(self.shard_dir.glob("worker_*.jsonl")):
                out.write(path.read_text(encoding="utf-8"))
        return {"merged_path": str(output), "record_merge_time_seconds": round(time.time() - started, 6)}

    def summary(self) -> Dict[str, Any]:
        return {
            "buffered_record_count": self.buffered_record_count,
            "flush_count": self.flush_count,
            "checkpoint_count": self.checkpoint_count,
            "partial_checkpoint_count": self.partial_checkpoint_count,
            "record_write_time_seconds": round(self.record_write_time_seconds, 6),
            "runtime_tmp_dir": str(self.runtime_tmp_dir),
            "final_records_dir": str(self.final_records_dir),
        }

