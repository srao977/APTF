from __future__ import annotations

from dataclasses import dataclass

from aptf_d01.evaluation.fmo_capture import FMOCaptureRecord


@dataclass
class RealizedOutcome:
    capture_id: str
    realized_return: float
    maximum_favorable_excursion: float
    maximum_adverse_excursion: float
    realized_direction: float
    time_to_max_favorable_excursion: float
    time_to_max_adverse_excursion: float
    reversal_occurred: bool
    realized_persistence: float


def evaluate_capture(capture: FMOCaptureRecord, forward_prices: list[tuple[float, float]], entry_price: float) -> RealizedOutcome:
    if not forward_prices:
        return RealizedOutcome(
            capture_id=capture.capture_id,
            realized_return=0.0,
            maximum_favorable_excursion=0.0,
            maximum_adverse_excursion=0.0,
            realized_direction=0.0,
            time_to_max_favorable_excursion=0.0,
            time_to_max_adverse_excursion=0.0,
            reversal_occurred=False,
            realized_persistence=0.0,
        )

    returns = [((p / entry_price) - 1.0) for _, p in forward_prices]
    mfe = max(returns)
    mae = min(returns)
    i_mfe = returns.index(mfe)
    i_mae = returns.index(mae)
    t0 = forward_prices[0][0]
    t_mfe = forward_prices[i_mfe][0] - t0
    t_mae = forward_prices[i_mae][0] - t0
    realized = returns[-1]
    direction = 1.0 if realized > 0 else (-1.0 if realized < 0 else 0.0)

    reversal = False
    if capture.directional_support >= 0 and mae < -0.001:
        reversal = True
    if capture.directional_support < 0 and mfe > 0.001:
        reversal = True

    persistence = max(0.0, min(1.0, 1.0 - abs(realized - returns[0]) / (abs(returns[0]) + 1e-6)))

    return RealizedOutcome(
        capture_id=capture.capture_id,
        realized_return=realized,
        maximum_favorable_excursion=mfe,
        maximum_adverse_excursion=mae,
        realized_direction=direction,
        time_to_max_favorable_excursion=t_mfe,
        time_to_max_adverse_excursion=t_mae,
        reversal_occurred=reversal,
        realized_persistence=persistence,
    )
