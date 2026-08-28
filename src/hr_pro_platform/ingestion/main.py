import sys
import time

from consumer import run_consumer
from error_handler import get_logger

logger = get_logger("main")

MAX_RETRIES = 5
BASE_DELAY = 1


def main():
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Starting HR Pro ingestion service (attempt {attempt}/{MAX_RETRIES})")
            run_consumer()
            break
        except Exception as e:
            delay = BASE_DELAY * (2 ** (attempt - 1))
            logger.error(f"Fatal error on attempt {attempt}: {e}")
            if attempt == MAX_RETRIES:
                logger.error("Max retries reached — shutting down")
                sys.exit(1)
            logger.info(f"Retrying in {delay}s...")
            time.sleep(delay)


if __name__ == "__main__":
    main()
