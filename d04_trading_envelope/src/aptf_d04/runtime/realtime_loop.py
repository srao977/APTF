from __future__ import annotations

import json
import time
from pathlib import Path

from aptf_d04.models.events import Event
from aptf_d04.models.enums import EventType
from aptf_d04.runtime.audit_log import AuditLogger
from aptf_d04.runtime.event_bus import EventBus

try:
    from rich.console import Console
except Exception:
    Console = None


class RealtimeLoop:
    def __init__(
        self,
        envelope,
        event_bus: EventBus,
        audit_logger: AuditLogger,
        speed: float,
        verbose: bool = False,
    ) -> None:
        self.envelope = envelope
        self.event_bus = event_bus
        self.audit_logger = audit_logger
        self.speed = speed
        self.verbose = verbose
        self.console = Console() if Console else None

    def _print_line(self, text: str) -> None:
        if self.console:
            self.console.print(text)
        else:
            print(text)

    def run(self, observations: list) -> dict:
        event_counter: dict[str, int] = {}
        prev_time = None
        states: list[str] = []
        transitions: list[str] = []
        captures: list[float] = []
        shapes: list[float] = []
        bases: list[float] = []
        gates: list[float] = []

        for obs in observations:
            rs = obs.return_shape
            ctx = obs.context

            evaluation = self.envelope.process(rs, ctx)
            states.append(evaluation.new_state.value)
            transitions.append(f"{evaluation.previous_state.value}->{evaluation.new_state.value}")
            captures.append(evaluation.capturability_score)
            shapes.append(evaluation.shape_quality)
            bases.append(evaluation.base_capturability_score)
            gates.append(evaluation.feasibility_gate_score)

            for evt in evaluation.events_emitted:
                event_counter[evt.value] = event_counter.get(evt.value, 0) + 1
                self.event_bus.publish(
                    Event(
                        event_type=evt,
                        timestamp=rs.timestamp,
                        candidate_id=rs.candidate_id,
                        return_shape_id=rs.return_shape_id,
                        payload={"state": evaluation.new_state.value},
                    )
                )

            self.audit_logger.write(
                scenario_time=obs.scenario_time,
                return_shape=rs,
                context=ctx,
                evaluation=evaluation,
            )

            line = (
                f"[{obs.scenario_time:.1f}s] {rs.candidate_id} {rs.return_shape_id} v{rs.version} "
                f"shape={rs.shape_quality:.2f} base={evaluation.base_capturability_score:.2f} "
                f"gate={evaluation.feasibility_gate_score:.2f} capture={evaluation.capturability_score:.2f} "
                f"aperture={evaluation.aperture:.2f} state={evaluation.previous_state.value}->{evaluation.new_state.value}"
            )
            if self.verbose or evaluation.opportunity_event is not None:
                events_joined = ",".join([e.value for e in evaluation.events_emitted])
                line = f"{line} events={events_joined}"
            self._print_line(line)

            if self.speed > 0 and prev_time is not None:
                dt = max(0.0, obs.scenario_time - prev_time)
                sleep_seconds = dt / self.speed
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
            prev_time = obs.scenario_time

        summary = {
            "final_state": self.envelope.current_state.value,
            "events": event_counter,
            "states": states,
            "transitions": transitions,
            "captures": captures,
            "shapes": shapes,
            "bases": bases,
            "gates": gates,
            "event_summary_checksum": json.dumps(event_counter, sort_keys=True),
        }
        return summary


def benchmark_observations(loop: RealtimeLoop, observations: list, output_path: Path) -> float:
    if output_path.exists():
        output_path.unlink()
    start = time.perf_counter()
    loop.run(observations)
    end = time.perf_counter()
    return end - start
