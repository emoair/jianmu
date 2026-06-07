from __future__ import annotations

import inspect
from typing import Any, Dict

from jianmu.extended_emitter_c import ExtendedEmitterC
from jianmu.self_learning.darwinforge import atomic_synthesis_policy_bridge, real_ir_emitter_validation


def detect_template_bypass() -> Dict[str, Any]:
    bridge_source = inspect.getsource(atomic_synthesis_policy_bridge)
    validation_source = inspect.getsource(real_ir_emitter_validation)
    emitter_source = inspect.getsource(ExtendedEmitterC)
    direct_renderer = "render_forgefrontier_c_source" in bridge_source or "render_forgefrontier_c_source" in validation_source
    marker_direct = "target_ir" in validation_source and "ExtendedEmitterC().emit" not in validation_source
    hardcoded_stdout_only = 'printf("%d\\n", value)' in emitter_source or "stdout_only" in bridge_source
    summary_only = "summary_only_validation_detected\": True" in validation_source
    return {
        "template_bypass_detected": direct_renderer,
        "marker_ir_direct_compile_detected": marker_direct,
        "hardcoded_stdout_only_c_program_detected": hardcoded_stdout_only,
        "summary_only_validation_detected": summary_only,
        "extended_ir_emitter_path_allowed": not direct_renderer and "ExtendedEmitterC().emit" in validation_source,
    }

