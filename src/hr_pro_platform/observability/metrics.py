from __future__ import annotations

import math
import os
from collections.abc import Iterator
from dataclasses import dataclass
from http.server import HTTPServer

from prometheus_client import CollectorRegistry, start_http_server
from prometheus_client.core import CounterMetricFamily, HistogramMetricFamily


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
PERSISTENCE_DURATION_SECONDS = "hr_pro_platform_ingestion_persistence_duration_seconds"
METRICS_HOST = os.getenv("INGESTION_METRICS_HOST", "0.0.0.0")
METRICS_PORT = int(os.getenv("INGESTION_METRICS_PORT", "9464"))


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


class IngestionMetricsCollector:
    """Adapt the existing process-local metrics to Prometheus exposition."""

    def __init__(self, counter: MonotonicCounter, processing: Histogram, persistence: Histogram):
        self._counter = counter
        self._processing = processing
        self._persistence = persistence

    def collect(self) -> Iterator[CounterMetricFamily | HistogramMetricFamily]:
        consumed = CounterMetricFamily(
            CONSUMED_MESSAGES_TOTAL,
            "Number of successfully fetched Kafka messages.",
        )
        consumed.add_metric([], self._counter.value)
        yield consumed

        for metric in (self._processing, self._persistence):
            yield HistogramMetricFamily(
                metric.name,
                f"Observed duration for {metric.name}.",
                buckets=[("+Inf", metric.count)],
                sum_value=metric.total,
            )


def create_ingestion_registry(
    counter: MonotonicCounter,
    processing: Histogram,
    persistence: Histogram,
) -> CollectorRegistry:
    registry = CollectorRegistry(auto_describe=True)
    registry.register(IngestionMetricsCollector(counter, processing, persistence))
    return registry


def start_metrics_server(
    registry: CollectorRegistry,
    host: str = METRICS_HOST,
    port: int = METRICS_PORT,
) -> tuple[HTTPServer, object]:
    """Start the process-local Prometheus exposition endpoint."""

    return start_http_server(port, addr=host, registry=registry)


def stop_metrics_server(server: tuple[HTTPServer, object]) -> None:
    http_server, _thread = server
    http_server.shutdown()
    http_server.server_close()
