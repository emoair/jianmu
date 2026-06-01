from __future__ import annotations

from pathlib import Path
from typing import Dict

from jianmu.self_learning.darwinforge.contrastive_forge_generator import generate_contrastive_forge_dataset


def generate_redqueen_v2_curriculum(output_dir: str | Path) -> Dict[str, object]:
    return generate_contrastive_forge_dataset(output_dir)
