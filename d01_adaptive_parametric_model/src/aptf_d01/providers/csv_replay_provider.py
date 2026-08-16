from __future__ import annotations

from pathlib import Path
import csv

from aptf_d01.models.enums import SessionState
from aptf_d01.models.normalized_observation import NormalizedObservation


class CSVReplayProvider:
    def __init__(self, csv_file: Path, entity_id: str = "TEST_ENTITY", source_id: str = "csv_replay") -> None:
        self.csv_file = csv_file
        self.entity_id = entity_id
        self.source_id = source_id

    def stream(self) -> list[NormalizedObservation]:
        rows: list[NormalizedObservation] = []
        with self.csv_file.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = {str(n).strip() for n in (reader.fieldnames or [])}
            has_bid_col = "bid" in fieldnames
            has_ask_col = "ask" in fieldnames
            has_bid_size_col = "bid_size" in fieldnames
            has_ask_size_col = "ask_size" in fieldnames
            has_trade_size_col = "trade_size" in fieldnames

            for i, row in enumerate(reader):
                ts = float(row.get("timestamp", i))
                price = float(row.get("price", 0.0))
                volume = float(row.get("volume", 1.0))

                bid = float(row["bid"]) if has_bid_col and row.get("bid") not in (None, "") else None
                ask = float(row["ask"]) if has_ask_col and row.get("ask") not in (None, "") else None
                bid_size = float(row["bid_size"]) if has_bid_size_col and row.get("bid_size") not in (None, "") else None
                ask_size = float(row["ask_size"]) if has_ask_size_col and row.get("ask_size") not in (None, "") else None
                trade_size = float(row["trade_size"]) if has_trade_size_col and row.get("trade_size") not in (None, "") else None

                rows.append(
                    NormalizedObservation(
                        entity_id=self.entity_id,
                        event_id=f"CSV-{i:07d}",
                        source_id=self.source_id,
                        source_sequence=i,
                        exchange_timestamp=ts,
                        receive_timestamp=float(row.get("receive_timestamp", ts)),
                        model_available_timestamp=float(row.get("model_available_timestamp", ts)),
                        price=price,
                        trade_size=trade_size,
                        volume=volume,
                        bid=bid,
                        ask=ask,
                        bid_size=bid_size,
                        ask_size=ask_size,
                        session_state=SessionState(str(row.get("session_state", "OPEN"))),
                        data_valid=bool(row.get("data_valid", True)),
                        channel_availability={
                            "price": True,
                            "volume": True,
                            "bid": bid is not None,
                            "ask": ask is not None,
                            "bid_size": bid_size is not None,
                            "ask_size": ask_size is not None,
                            "trade_size": trade_size is not None,
                        },
                        metadata={"replay_file": str(self.csv_file)},
                    )
                )
        return rows
