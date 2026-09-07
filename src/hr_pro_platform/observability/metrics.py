from __future__ import annotations

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
