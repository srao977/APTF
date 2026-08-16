from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator
from zoneinfo import ZoneInfo

from d01.v02.observations import NormalizedObservation

from .constants import PRIMARY_START, RESERVE_START


@dataclass(frozen=True)
class HistoricalRow:
    source_row_id: int
    event_time: datetime
    local_time: datetime
    close: float
    volume: float
    session: str
    observation: NormalizedObservation


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("NAIVE_TIMESTAMP")
    return parsed


def transition_stratum(previous: HistoricalRow | None, current: HistoricalRow) -> str:
    if previous is None:
        return "START"
    day_delta = (current.local_time.date() - previous.local_time.date()).days
    elapsed = (current.event_time - previous.event_time).total_seconds()
    if day_delta >= 2:
        return "WEEKEND_OR_HOLIDAY_GAP"
    if day_delta == 1:
        return "OVERNIGHT_GAP"
    if current.session != previous.session:
        return "SESSION_TRANSITION"
    if elapsed > 60.0:
        return "DATA_GAP/IRREGULAR_INTERVAL"
    if 0.0 < elapsed <= 60.0:
        return "INTRASESSION_CONTINUOUS"
    raise ValueError("NON_MONOTONIC_EVENT_TIME")


def iter_primary_csv(path: Path) -> Iterator[HistoricalRow]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        header_line = handle.readline()
        header = next(csv.reader([header_line]))
        index = {name: position for position, name in enumerate(header)}
        timestamp_position = index["event_timestamp_utc"]
        accepted = 0
        previous_time: datetime | None = None
        for source_row_id, line in enumerate(handle, start=2):
            # The normalized schema's timestamp fields contain no commas. Extract only
            # the UTC timestamp before CSV parsing can expose any reserve field value.
            prefix = line.split(",", timestamp_position + 1)
            if len(prefix) <= timestamp_position:
                raise ValueError("MALFORMED_TIMESTAMP_PREFIX")
            event_time = parse_timestamp(prefix[timestamp_position].strip().strip('"'))
            if event_time >= RESERVE_START:
                break
            if event_time < PRIMARY_START:
                continue
            raw = next(csv.reader([line]))
            if previous_time is not None and event_time <= previous_time:
                raise ValueError("NON_MONOTONIC_EVENT_TIME")
            previous_time = event_time
            valid = raw[index["data_valid"]].strip().lower() == "true"
            close_text = raw[index["close"]].strip()
            volume_text = raw[index["volume"]].strip()
            if not valid or not close_text or not volume_text:
                continue
            close = float(close_text)
            volume = float(volume_text)
            accepted += 1
            local_time = event_time.astimezone(ZoneInfo("America/New_York"))
            session = raw[index["session_type"]]
            observation = NormalizedObservation(
                entity_id="SPY", event_time=event_time.timestamp(), receive_time=event_time.timestamp(),
                sequence_id=accepted, price=close, volume=volume, session=session, source_quality=1.0,
                availability_mask={"price": True, "volume": True, "bid": False, "ask": False},
            )
            yield HistoricalRow(source_row_id, event_time, local_time, close, volume, session, observation)


def resolve_first_at_or_after(times: list[float], anchor_index: int, target_minutes: float, boundary_epoch: float) -> tuple[int | None, float | None, str]:
    target = times[anchor_index] + target_minutes * 60.0
    if target >= boundary_epoch:
        return None, None, "RIGHT_CENSORED"
    import bisect
    endpoint = bisect.bisect_left(times, target, lo=anchor_index + 1)
    if endpoint >= len(times) or times[endpoint] >= boundary_epoch:
        return None, None, "RIGHT_CENSORED"
    return endpoint, (times[endpoint] - times[anchor_index]) / 60.0, "EXACT"