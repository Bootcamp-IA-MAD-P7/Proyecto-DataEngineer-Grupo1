from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class MonotonicCounter:
    """Small process-local counter for metrics exported by a later task."""

    name: str
    _value: int = 0

    def increment(self, amount: int = 1) -> None:
        if amount < 1:
            raise ValueError("counter increments must be positive")
        self._value += amount

    @property
    def value(self) -> int:
        return self._value


CONSUMED_MESSAGES_TOTAL = "hr_pro_platform_ingestion_messages_consumed_total"
PROCESSING_DURATION_SECONDS = "hr_pro_platform_ingestion_processing_duration_seconds"


@dataclass
class Histogram:
    """Small process-local timer metric for later external exposition."""

    name: str
    count: int = 0
    total: float = 0.0

    def observe(self, value: float) -> None:
        if not math.isfinite(value) or value < 0:
            raise ValueError("histogram observations must be finite and non-negative")
        self.count += 1
        self.total += value
