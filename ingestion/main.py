from consumer import run_consumer
from error_handler import get_logger

logger = get_logger("main")

if __name__ == "__main__":
    logger.info("Starting HR Pro ingestion service")
    run_consumer()
