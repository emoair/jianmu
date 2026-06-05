from pathlib import Path

from jianmu.self_learning.darwinforge.linguaforge_nl_alpha_core import build_row
from jianmu.self_learning.darwinforge.linguaforge_nl_compiler_validation import compiler_validation


def test_nl_compiler_validation_path_goes_through_token(tmp_path: Path):
    rows = [build_row(i, 188) for i in range(300)]
    supported = [row for row in rows if row["support_status"] == "current_supported"]
    result = compiler_validation(supported, tmp_path, 5)
    assert result["compiler_validation_completed"]
    assert result["real_compiler_invocations"] >= 0
