"""Per-request PostgreSQL connection dependency for the API.

See docs/specs/HRP-83-postgres-query-api.md. Reuses the same
``POSTGRES_*`` environment variables ``storage/config.py`` already
validates -- no new configuration surface. Opens one connection per
request and closes it afterwards; connection pooling is deliberately
deferred to a follow-up task once real query endpoints exist (see the
spec's "What stays provisional" section).
"""

from __future__ import annotations

from collections.abc import Iterator

import psycopg

from ..storage.config import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)


def get_connection() -> Iterator[psycopg.Connection[tuple[object, ...]]]:
    """FastAPI dependency yielding one PostgreSQL connection per request."""

    connection = psycopg.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        connect_timeout=5,
    )
    try:
        yield connection
    finally:
        connection.close()
