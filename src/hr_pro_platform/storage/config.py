import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")


def _require(var: str) -> str:
    value = os.getenv(var)
    if value is None:
        raise OSError(f"Missing required environment variable: {var}")
    return value


POSTGRES_HOST = _require("POSTGRES_HOST")
POSTGRES_PORT = _require("POSTGRES_PORT")
POSTGRES_DB = _require("POSTGRES_DB")
POSTGRES_USER = _require("POSTGRES_USER")
POSTGRES_PASSWORD = _require("POSTGRES_PASSWORD")
