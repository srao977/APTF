from __future__ import annotations

from pathlib import Path
import random

import yaml

from aptf_d01.models.enums import SessionState
from aptf_d01.models.normalized_observation import NormalizedObservation


class SyntheticProvider:
    def __init__(self, scenario_file: Path, entity_id: str = "TEST_ENTITY") -> None:
        self.scenario_file = scenario_file
        self.entity_id = entity_id

    def stream(self) -> list[NormalizedObservation]:
        data = yaml.safe_load(self.scenario_file.read_text(encoding="utf-8"))
        seed = int(data.get("seed", 0))
        steps = int(data.get("steps", 100))
        base_price = float(data.get("base_price", 100.0))
        base_volume = float(data.get("base_volume", 1000.0))
        dt = float(data.get("dt_seconds", 1.0))
        spread = float(data.get("spread", 0.02))
        rng = random.Random(seed)

        price = base_price
        t = 0.0
        rows: list[NormalizedObservation] = []
        volume_shocks = {int(s["step"]): float(s["multiplier"]) for s in data.get("volume_shocks", [])}
        price_shocks = {int(s["step"]): float(s["displacement"]) for s in data.get("price_shocks", [])}
        reversal_step = data.get("reversal_step")
        reversal_drift = float(data.get("reversal_drift", 0.0))

        for i in range(steps):
            if data.get("irregular_dt", False):
                t += max(0.1, dt + rng.uniform(-0.7, 1.4))
            else:
                t += dt

            drift = float(data.get("price_drift", 0.0))
            if reversal_step is not None and i >= int(reversal_step):
                drift = reversal_drift

            noise = float(data.get("price_noise", 0.0)) * rng.uniform(-1.0, 1.0)
            displacement = price_shocks.get(i, 0.0)
            price = max(0.01, price * (1.0 + drift + noise + displacement))

            vol_noise = float(data.get("volume_noise", 0.0)) * rng.uniform(-1.0, 1.0)
            vol_mul = float(data.get("volume_trend_multiplier", 1.0))
            volume = max(1.0, base_volume * vol_mul + vol_noise)
            if i in volume_shocks:
                volume *= volume_shocks[i]

            bid = max(0.01, price - spread * 0.5)
            ask = price + spread * 0.5
            trade_size = max(1.0, volume * 0.01)

            rows.append(
                NormalizedObservation(
                    entity_id=self.entity_id,
                    event_id=f"EV-{i:07d}",
                    source_id="synthetic",
                    source_sequence=i,
                    exchange_timestamp=t,
                    receive_timestamp=t + 0.001,
                    model_available_timestamp=t + 0.002,
                    price=price,
                    trade_size=trade_size,
                    volume=volume,
                    bid=bid,
                    ask=ask,
                    bid_size=max(1.0, volume * 0.45),
                    ask_size=max(1.0, volume * 0.55),
                    session_state=SessionState.OPEN,
                    data_valid=True,
                    metadata={"scenario": data.get("name", "unknown")},
                )
            )
        return rows
