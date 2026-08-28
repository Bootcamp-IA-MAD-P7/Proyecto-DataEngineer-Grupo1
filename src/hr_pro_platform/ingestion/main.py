import sys
import time

from consumer import run_consumer
from error_handler import get_logger

logger = get_logger("main")

MAX_RETRIES = 5


def main():
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(
                f"Starting HR Pro ingestion service (attempt {attempt}/{MAX_RETRIES})"
            )
            run_consumer()
            break
        except Exception as e:
            wait = 2 ** (attempt - 1)
            logger.error(
                f"Consumer failed on attempt {attempt}/{MAX_RETRIES}: {e} "
                f"| retrying in {wait}s"
            )
            if attempt < MAX_RETRIES:
                time.sleep(wait)
            else:
                logger.error("Max retries reached — shutting down")
                sys.exit(1)


if __name__ == "__main__":
    main()
