from __future__ import annotations

from dataclasses import dataclass

from aptf_d04.models.enums import EnvelopeState


@dataclass
class HysteresisConfig:
    open_threshold: float
    close_threshold: float
    open_persistence_observations: int
    close_persistence_observations: int

    def validate(self) -> None:
        if not (0.0 <= self.open_threshold <= 1.0):
            raise ValueError("open_threshold must be in [0,1]")
        if not (0.0 <= self.close_threshold <= 1.0):
            raise ValueError("close_threshold must be in [0,1]")
        if self.open_threshold <= self.close_threshold:
            raise ValueError("open_threshold must be greater than close_threshold")
        if self.open_persistence_observations < 1:
            raise ValueError("open_persistence_observations must be >= 1")
        if self.close_persistence_observations < 1:
            raise ValueError("close_persistence_observations must be >= 1")


class HysteresisController:
    def __init__(self, config: HysteresisConfig) -> None:
        config.validate()
        self.config = config
        self.consecutive_open_qualifying = 0
        self.consecutive_close_qualifying = 0

    def reset(self) -> None:
        self.consecutive_open_qualifying = 0
        self.consecutive_close_qualifying = 0

    def next_state(
        self,
        current_state: EnvelopeState,
        capturability_score: float,
    ) -> tuple[EnvelopeState, list[str]]:
        reasons: list[str] = []
        open_qual = capturability_score >= self.config.open_threshold
        close_qual = capturability_score <= self.config.close_threshold

        if current_state == EnvelopeState.CLOSED:
            if open_qual:
                self.consecutive_open_qualifying = 1
                self.consecutive_close_qualifying = 0
                reasons.append("THRESHOLD_OPEN_PENDING")
                return EnvelopeState.OPENING, reasons
            self.reset()
            return EnvelopeState.CLOSED, reasons

        if current_state == EnvelopeState.OPENING:
            if open_qual:
                self.consecutive_open_qualifying += 1
                reasons.append("THRESHOLD_OPEN_PENDING")
                if self.consecutive_open_qualifying >= self.config.open_persistence_observations:
                    self.consecutive_open_qualifying = 0
                    reasons.append("OPEN_PERSISTENCE_MET")
                    return EnvelopeState.OPEN, reasons
                return EnvelopeState.OPENING, reasons
            self.reset()
            return EnvelopeState.CLOSED, reasons

        if current_state == EnvelopeState.OPEN:
            if close_qual:
                self.consecutive_close_qualifying = 1
                self.consecutive_open_qualifying = 0
                reasons.append("THRESHOLD_CLOSE_PENDING")
                return EnvelopeState.CLOSING, reasons
            self.consecutive_close_qualifying = 0
            return EnvelopeState.OPEN, reasons

        if current_state == EnvelopeState.CLOSING:
            if close_qual:
                self.consecutive_close_qualifying += 1
                reasons.append("THRESHOLD_CLOSE_PENDING")
                if self.consecutive_close_qualifying >= self.config.close_persistence_observations:
                    self.consecutive_close_qualifying = 0
                    reasons.append("CLOSE_PERSISTENCE_MET")
                    return EnvelopeState.CLOSED, reasons
                return EnvelopeState.CLOSING, reasons
            self.consecutive_close_qualifying = 0
            return EnvelopeState.OPEN, reasons

        return current_state, reasons
