from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from aptf_d04.inputs.scenario_loader import load_yaml


class RuntimeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_loop_speed: float = Field(ge=0.0)


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

    capturability_model_version: str = "V0_2"

    @model_validator(mode="after")
    def _weights(self) -> "CapturabilitySettings":
        if self.capturability_model_version != "V0_2":
            raise ValueError("capturability_model_version must be V0_2")
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
