from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass
class RunningStatistics:
    count: int = 0
    mean: float = 0.0
    m2: float = 0.0
    version: int = 0

    def std(self) -> float:
        if self.count <= 1:
            return 0.0
        var = self.m2 / float(self.count - 1)
        return math.sqrt(max(0.0, var))

    def update(self, value: float) -> None:
        self.version += 1
        self.count += 1
        delta = value - self.mean
        self.mean += delta / float(self.count)
        delta2 = value - self.mean
        self.m2 += delta * delta2
