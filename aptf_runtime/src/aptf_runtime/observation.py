from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Mapping


REQUIRED_SOURCE_FIELDS = (
    "entity_id",
    "event_timestamp_local",
    "event_timestamp_utc",
    "timezone",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "session_type",
    "source_provider",
    "source_dataset",
    "source_row_number",
    "data_valid",
    "quality_flags",
)


@dataclass(frozen=True)
class Observation:
    entity_id: str
    physical_row: int
    source_row_number: str
    event_timestamp_local: str
    event_timestamp_utc: str
    timezone: str
    open: str
    high: str
    low: str
    close: str
    volume: str
    session_type: str
    source_provider: str
    source_dataset: str
    data_valid: bool
    quality_flags: str

    @classmethod
    def from_source_row(cls, physical_row: int, source_row: Mapping[str, str]) -> "Observation":
        missing = [name for name in REQUIRED_SOURCE_FIELDS if name not in source_row]
        if missing:
            raise ValueError(f"missing required source fields: {', '.join(missing)}")
        if physical_row < 2:
            raise ValueError("physical_row must include the CSV header offset")
        if source_row["data_valid"].lower() != "true":
            raise ValueError("source observation failed data validation")
        timestamp = datetime.fromisoformat(source_row["event_timestamp_utc"].replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise ValueError("event_timestamp_utc must be timezone-aware")
        for name in ("open", "high", "low", "close", "volume"):
            if not math.isfinite(float(source_row[name])):
                raise ValueError(f"{name} must be finite")
        return cls(
            entity_id=source_row["entity_id"],
            physical_row=physical_row,
            source_row_number=source_row["source_row_number"],
            event_timestamp_local=source_row["event_timestamp_local"],
            event_timestamp_utc=source_row["event_timestamp_utc"],
            timezone=source_row["timezone"],
            open=source_row["open"],
            high=source_row["high"],
            low=source_row["low"],
            close=source_row["close"],
            volume=source_row["volume"],
            session_type=source_row["session_type"],
            source_provider=source_row["source_provider"],
            source_dataset=source_row["source_dataset"],
            data_valid=True,
            quality_flags=source_row["quality_flags"],
        )

    @property
    def event_time(self) -> float:
        return datetime.fromisoformat(
            self.event_timestamp_utc.replace("Z", "+00:00")
        ).timestamp()

    def to_d01(self):
        from d01.v02.observations import NormalizedObservation

        return NormalizedObservation(
            entity_id=self.entity_id,
            event_time=self.event_time,
            receive_time=self.event_time,
            sequence_id=self.physical_row - 2,
            price=float(self.close),
            volume=float(self.volume),
            bid=None,
            ask=None,
            session=self.session_type,
            source_quality=1.0,
            availability_mask={"price": True, "volume": True},
        )
