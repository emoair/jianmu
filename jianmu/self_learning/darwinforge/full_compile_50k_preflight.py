from pathlib import Path
from typing import Union

from jianmu.self_learning.darwinforge.full_compile_50k_continuation_core import write_preflight


def write_full_compile_50k_preflight(output_records: Union[str, Path]):
    return write_preflight(Path(output_records), after=False)


__all__ = ["write_full_compile_50k_preflight"]
