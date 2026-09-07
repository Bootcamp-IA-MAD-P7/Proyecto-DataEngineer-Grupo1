from __future__ import annotations

from http.client import HTTPResponse
from urllib.request import urlopen

from prometheus_client import generate_latest

from hr_pro_platform.observability.metrics import (
    CONSUMED_MESSAGES_TOTAL,
    PERSISTENCE_DURATION_SECONDS,
    PROCESSING_DURATION_SECONDS,
    Histogram,
    MonotonicCounter,
    create_ingestion_registry,
    start_metrics_server,
    stop_metrics_server,
)


def _metrics_fixture() -> tuple[MonotonicCounter, Histogram, Histogram]:
    counter = MonotonicCounter(CONSUMED_MESSAGES_TOTAL)
    processing = Histogram(PROCESSING_DURATION_SECONDS)
    persistence = Histogram(PERSISTENCE_DURATION_SECONDS)
    counter.increment(2)
    processing.observe(0.5)
    persistence.observe(0.25)
    return counter, processing, persistence


def test_hrp80_registry_exposes_existing_metric_families_and_state() -> None:
    counter, processing, persistence = _metrics_fixture()
    registry = create_ingestion_registry(counter, processing, persistence)

    exposition = generate_latest(registry).decode("utf-8")

    assert f"{CONSUMED_MESSAGES_TOTAL} 2.0" in exposition
    assert f"{PROCESSING_DURATION_SECONDS}_count 1.0" in exposition
    assert f"{PROCESSING_DURATION_SECONDS}_sum 0.5" in exposition
    assert f"{PERSISTENCE_DURATION_SECONDS}_count 1.0" in exposition
    assert f"{PERSISTENCE_DURATION_SECONDS}_sum 0.25" in exposition
    assert exposition.count(f"# TYPE {CONSUMED_MESSAGES_TOTAL} counter") == 1
    assert exposition.count(f"# TYPE {PROCESSING_DURATION_SECONDS} histogram") == 1
    assert exposition.count(f"# TYPE {PERSISTENCE_DURATION_SECONDS} histogram") == 1


def test_hrp80_http_exposition_uses_prometheus_text_format_and_closes() -> None:
    counter, processing, persistence = _metrics_fixture()
    registry = create_ingestion_registry(counter, processing, persistence)
    server = start_metrics_server(registry, host="127.0.0.1", port=0)
    try:
        response: HTTPResponse
        with urlopen(f"http://127.0.0.1:{server[0].server_port}/metrics") as response:
            body = response.read().decode("utf-8")
            content_type = response.headers["Content-Type"]
        assert response.status == 200
        assert content_type is not None
        assert content_type.startswith("text/plain")
        assert f"{CONSUMED_MESSAGES_TOTAL} 2.0" in body
    finally:
        stop_metrics_server(server)
