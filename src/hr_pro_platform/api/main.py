"""FastAPI application skeleton for the PostgreSQL query API.

See docs/specs/HRP-83-postgres-query-api.md. This module intentionally
exposes no business endpoint -- only the application factory, a shared
database-error handler, and a ``/health`` check proving the skeleton
connects to PostgreSQL. HRP-84/85/86 add their own business endpoints
on top of this skeleton in their own tasks; HRP-89 is the Streamlit
frontend that will consume them.
"""

from __future__ import annotations

from typing import Annotated, Any

import psycopg
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from ..ingestion.error_handler import get_logger
from .db import get_connection

logger = get_logger("api")


def create_app() -> FastAPI:
    """Build the FastAPI application. A factory (not a bare module-level
    app) keeps the skeleton testable: tests build their own app instance
    and override ``get_connection`` instead of monkeypatching a shared
    global.
    """

    app = FastAPI(title="HR Pro Data Platform API")

    @app.exception_handler(psycopg.Error)
    async def _database_error_handler(request: Request, error: Exception) -> JSONResponse:
        assert isinstance(error, psycopg.Error)
        # Log only allowlisted, non-sensitive metadata: a database error's
        # message/DETAIL can echo rejected values, per
        # docs/backend-standards.md ("Must not: Log sensitive payloads") --
        # the same discipline storage/person_repository.py already follows.
        sqlstate = getattr(error, "sqlstate", None)
        logger.error(
            "Database error handling request | path=%s error_class=%s sqlstate=%s",
            request.url.path,
            type(error).__name__,
            sqlstate,
        )
        return JSONResponse(status_code=503, content={"status": "unavailable"})

    @app.get("/health")
    def health(
        connection: Annotated[psycopg.Connection[tuple[Any, ...]], Depends(get_connection)],
    ) -> dict[str, str]:
        connection.execute("SELECT 1")
        return {"status": "ok"}

    return app


app = create_app()
