"""Command-line entry point for the Kafka consumer."""

from .consumer import ShutdownController, install_signal_handlers, run_consumer
from .error_handler import get_logger

logger = get_logger(__name__)


def main() -> None:
    controller = ShutdownController()
    install_signal_handlers(controller)
    logger.info("Starting HR Pro Kafka ingestion service")
    run_consumer(should_continue=controller)


if __name__ == "__main__":
    main()
