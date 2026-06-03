from pathlib import Path

from jianmu.self_learning.darwinforge.full_compile_50k_continuation_core import write_preflight


def write_full_compile_50k_postflight(output_records: str | Path):
    return write_preflight(Path(output_records), after=True)


__all__ = ["write_full_compile_50k_postflight"]
