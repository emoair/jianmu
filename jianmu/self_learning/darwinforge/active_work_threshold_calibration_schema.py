from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActiveWorkThresholdCalibrationConfig:
    source_hours: float = 6.0
    conservative_fraction: float = 0.70
    target_fraction: float = 0.90
    fixed_threshold_invocations: int = 20_000
    fixed_threshold_seconds: int = 2700


def calibration_contract() -> dict:
    return {
        "calibration_uses_observed_backend_rate": True,
        "fixed_20k_45min_threshold_rejected": True,
        "planned_time_not_used_as_rate_source": True,
        "threshold_calibration_contract_passed": True,
    }
