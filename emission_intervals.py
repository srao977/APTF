from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class IntervalState:
    engine: str
    symbol: str
    session_id: str
    color: str
    start_timestamp: str
    start_index: int
    last_timestamp: str
    last_index: int
    observation_count: int


@dataclass(frozen=True)
class CompletedInterval:
    engine: str
    symbol: str
    session_date: str
    color: str
    start_timestamp: str
    end_timestamp: str
    start_index: int
    end_index: int
    observation_count: int
    duration_minutes: int
    elapsed_seconds: float

    def as_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


class EmissionIntervalizer:
    def observe(
        self,
        engine_id: str,
        symbol: str,
        timestamp: str,
        categorical_state: str,
        session_id: str,
        observation_index: int,
        state: IntervalState | None,
    ) -> tuple[IntervalState, CompletedInterval | None, int]:
        if state is not None and timestamp <= state.last_timestamp:
            raise ValueError("timestamps must increase")
        elapsed_seconds = None
        if state is not None:
            current_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            previous_time = datetime.fromisoformat(state.last_timestamp.replace("Z", "+00:00"))
            elapsed_seconds = (current_time - previous_time).total_seconds()
        continues = (
            state is not None
            and state.session_id == session_id
            and state.color == categorical_state
            and elapsed_seconds == 60.0
        )
        if continues:
            current = IntervalState(
                engine=engine_id, symbol=symbol, session_id=session_id, color=categorical_state,
                start_timestamp=state.start_timestamp, start_index=state.start_index,
                last_timestamp=timestamp, last_index=observation_index,
                observation_count=state.observation_count + 1,
            )
            return current, None, current.observation_count
        completed = None if state is None else self.complete(state)
        current = IntervalState(
            engine=engine_id, symbol=symbol, session_id=session_id, color=categorical_state,
            start_timestamp=timestamp, start_index=observation_index,
            last_timestamp=timestamp, last_index=observation_index, observation_count=1,
        )
        return current, completed, 1

    def complete(self, state: IntervalState) -> CompletedInterval:
        start = datetime.fromisoformat(state.start_timestamp.replace("Z", "+00:00"))
        end = datetime.fromisoformat(state.last_timestamp.replace("Z", "+00:00"))
        return CompletedInterval(
            engine=state.engine, symbol=state.symbol, session_date=state.session_id.split(":", 1)[0],
            color=state.color, start_timestamp=state.start_timestamp, end_timestamp=state.last_timestamp,
            start_index=state.start_index, end_index=state.last_index,
            observation_count=state.observation_count, duration_minutes=state.observation_count,
            elapsed_seconds=(end - start).total_seconds(),
        )