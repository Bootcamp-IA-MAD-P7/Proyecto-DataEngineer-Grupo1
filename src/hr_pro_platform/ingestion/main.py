import sys
import time

from ..observability.metrics import (
    create_ingestion_registry,
    start_metrics_server,
    stop_metrics_server,
)
from .consumer import consumed_messages_counter, processing_duration_histogram, run_consumer
from .error_handler import get_logger
from .mongo import persistence_duration_histogram

logger = get_logger("main")

MAX_RETRIES = 5
BASE_DELAY = 1


def main() -> None:
    registry = create_ingestion_registry(
        consumed_messages_counter,
        processing_duration_histogram,
        persistence_duration_histogram,
    )
    metrics_server = start_metrics_server(registry)
    try:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"Starting HR Pro ingestion service (attempt {attempt}/{MAX_RETRIES})")
                run_consumer()
                break
            except Exception as error:
                delay = BASE_DELAY * (2 ** (attempt - 1))
                logger.error(f"Fatal error on attempt {attempt}: {error}")
                if attempt == MAX_RETRIES:
                    logger.error("Max retries reached — shutting down")
                    sys.exit(1)
                logger.info(f"Retrying in {delay}s...")
                time.sleep(delay)
    finally:
        stop_metrics_server(metrics_server)


if __name__ == "__main__":
    main()
