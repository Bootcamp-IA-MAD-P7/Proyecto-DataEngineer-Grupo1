"""FastAPI application for the PostgreSQL query API.

See docs/specs/HRP-83-postgres-query-api.md (skeleton: application
factory, shared database-error handler, ``/health``),
docs/specs/HRP-84-search-person-endpoint.md (``GET /people/search``,
the first business endpoint),
docs/specs/HRP-85-search-by-location-profession.md (``GET
/people/search/by-location-profession``) and
docs/specs/HRP-86-statistics-endpoint.md (``GET /statistics``). HRP-89
is the Streamlit frontend that will consume them.
"""

from __future__ import annotations

from typing import Annotated, Any

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from ..ingestion.error_handler import get_logger
from .db import get_connection
from .people import (
    ALLOWED_FILTERS,
    LOCATION_FILTERS,
    PROFESSIONAL_FILTERS,
    PersonSearchResult,
    search_employees,
    search_employees_by_location_or_profession,
)
from .statistics import StatisticsResult, compute_statistics

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

    @app.get("/people/search/by-location-profession")
    def search_people_by_location_or_profession(
        connection: Annotated[psycopg.Connection[tuple[Any, ...]], Depends(get_connection)],
        city: str | None = None,
        address: str | None = None,
        job: str | None = None,
        company: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[PersonSearchResult]:
        location_filters: dict[str, object] = {
            name: value
            for name, value in {"city": city, "address": address}.items()
            if value is not None
        }
        professional_filters: dict[str, object] = {
            name: value
            for name, value in {"job": job, "company": company}.items()
            if value is not None
        }
        # Both dicts' keys always come from these fixed, code-controlled
        # literals -- never from arbitrary caller-supplied names -- so
        # these assertions document the invariant
        # search_employees_by_location_or_profession() relies on rather
        # than guarding against untrusted input.
        assert set(location_filters).issubset(LOCATION_FILTERS)
        assert set(professional_filters).issubset(PROFESSIONAL_FILTERS)
        if not location_filters and not professional_filters:
            raise HTTPException(
                status_code=400,
                detail="At least one of city, address, job or company is required",
            )
        if not 1 <= limit <= 100:
            raise HTTPException(status_code=400, detail="limit must be between 1 and 100")
        if offset < 0:
            raise HTTPException(status_code=400, detail="offset must be non-negative")

        with connection.cursor() as cursor:
            return search_employees_by_location_or_profession(
                cursor,
                location_filters=location_filters,
                professional_filters=professional_filters,
                limit=limit,
                offset=offset,
            )

    @app.get("/statistics")
    def statistics(
        connection: Annotated[psycopg.Connection[tuple[Any, ...]], Depends(get_connection)],
    ) -> StatisticsResult:
        with connection.cursor() as cursor:
            return compute_statistics(cursor)

    return app


app = create_app()
