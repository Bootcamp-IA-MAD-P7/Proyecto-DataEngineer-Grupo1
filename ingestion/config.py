import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


def _require(var: str) -> str:
    value = os.getenv(var)
    if value is None:
        raise EnvironmentError(f"Missing required environment variable: {var}")
    return value


KAFKA_CONFIG = {
    "bootstrap.servers": _require("KAFKA_BOOTSTRAP_SERVERS"),
    "group.id": "hr-ingestion-group",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,
}

KAFKA_TOPICS = [
    "personal-data",
    "location",
    "professional-data",
    "bank-data",
    "net-data",
]

MONGO_URI = _require("MONGO_URI")
MONGO_DB = _require("MONGO_DB")
MONGO_COL = _require("MONGO_COL")
