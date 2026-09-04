"""FastAPI application for the PostgreSQL query API.

See docs/specs/HRP-83-postgres-query-api.md (skeleton: application
factory, shared database-error handler, ``/health``) and
docs/specs/HRP-84-search-person-endpoint.md (``GET /people/search``,
the first business endpoint). HRP-85/86 add their own business
endpoints on top of this skeleton in their own tasks; HRP-89 is the
Streamlit frontend that will consume them.
"""

from __future__ import annotations

from typing import Annotated, Any

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from ..ingestion.error_handler import get_logger
from .db import get_connection
from .people import ALLOWED_FILTERS, PersonSearchResult, search_employees

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

    @app.get("/people/search")
    def search_people(
        connection: Annotated[psycopg.Connection[tuple[Any, ...]], Depends(get_connection)],
        passport: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        id: Annotated[int | None, Query(alias="id")] = None,  # noqa: A002
        limit: int = 20,
        offset: int = 0,
    ) -> list[PersonSearchResult]:
        filters: dict[str, object] = {
            name: value
            for name, value in {
                "id": id,
                "passport": passport,
                "first_name": first_name,
                "last_name": last_name,
            }.items()
            if value is not None
        }
        # filters' keys always come from this fixed, code-controlled
        # dict literal -- never from arbitrary caller-supplied names --
        # so this assertion documents the invariant search_employees()
        # relies on rather than guarding against untrusted input.
        assert set(filters).issubset(ALLOWED_FILTERS)
        if not filters:
            raise HTTPException(
                status_code=400,
                detail="At least one of id, passport, first_name or last_name is required",
            )
        if not 1 <= limit <= 100:
            raise HTTPException(status_code=400, detail="limit must be between 1 and 100")
        if offset < 0:
            raise HTTPException(status_code=400, detail="offset must be non-negative")

        with connection.cursor() as cursor:
            return search_employees(cursor, filters=filters, limit=limit, offset=offset)

    return app


app = create_app()
