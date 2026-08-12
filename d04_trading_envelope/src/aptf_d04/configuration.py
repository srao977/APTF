from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from aptf_d04.inputs.scenario_loader import load_yaml


class RuntimeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_loop_speed: float = Field(ge=0.0)
    auto_open_position_on_qualified_opportunity: bool
    critical_data_integrity_threshold: float = Field(ge=0.0, le=1.0)


class HysteresisSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    open_threshold: float = Field(ge=0.0, le=1.0)
    close_threshold: float = Field(ge=0.0, le=1.0)
    open_persistence_observations: int = Field(ge=1)
    close_persistence_observations: int = Field(ge=1)

    @model_validator(mode="after")
    def _thresholds(self) -> "HysteresisSettings":
        if self.open_threshold <= self.close_threshold:
            raise ValueError("open_threshold must be greater than close_threshold")
        return self


class CapturabilitySettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capturability_model_version: str = "V0"
    target_lifetime_seconds: float = Field(gt=0.0)
    shape_weights: dict[str, float]
    envelope_weights: dict[str, float]
    feasibility_gate: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def _weights(self) -> "CapturabilitySettings":
        if abs(sum(self.shape_weights.values()) - 1.0) > 1e-6:
            raise ValueError("shape_weights must sum to 1")
        if abs(sum(self.envelope_weights.values()) - 1.0) > 1e-6:
            raise ValueError("envelope_weights must sum to 1")
        if self.capturability_model_version == "V0_2":
            mode = self.feasibility_gate.get("mode")
            dims = self.feasibility_gate.get("dimensions", [])
            threshold = self.feasibility_gate.get("warning_threshold")
            if mode != "minimum":
                raise ValueError("feasibility_gate.mode must be 'minimum' for V0_2")
            if not isinstance(dims, list) or len(dims) == 0:
                raise ValueError("feasibility_gate.dimensions must be a non-empty list for V0_2")
            if threshold is None or not (0.0 <= float(threshold) <= 1.0):
                raise ValueError("feasibility_gate.warning_threshold must be in [0,1] for V0_2")
        return self


class ApertureSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alpha: float = Field(ge=0.0, le=1.0)


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runtime: RuntimeConfig
    hysteresis: HysteresisSettings
    capturability: CapturabilitySettings
    aperture: ApertureSettings


def load_config(path: Path) -> AppConfig:
    data = load_yaml(path)
    return AppConfig(**data)
