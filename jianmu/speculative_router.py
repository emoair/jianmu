import re
from typing import List, Optional

from jianmu.hierarchical_router import HierarchicalSemanticRouter
from jianmu.ir import ProgramIR
from jianmu.routes import RouteCandidate


def _extract_literal_value(text: str) -> int:
    m = re.search(r"(?<![\w.])-?\d+", text)
    return int(m.group()) if m else 1


class SpeculativeRouter:
    """
    Compatibility facade for v0.4 callers.

    v0.5 moves candidate generation into HierarchicalSemanticRouter. This class
    still exposes the old generate_candidates method so existing tests and code
    keep working.
    """

    def __init__(self):
        self._hierarchical = HierarchicalSemanticRouter()

    def generate_candidates(
        self,
        user_input: str,
        previous_ir: Optional[ProgramIR] = None,
    ) -> List[RouteCandidate]:
        features = self._hierarchical.analyze(user_input, previous_ir)
        return self._hierarchical.generate_candidates(features, previous_ir)
