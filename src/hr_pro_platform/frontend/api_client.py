from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

_BASE_URL: str = os.getenv("HRP_API_BASE_URL", "http://127.0.0.1:8123").rstrip("/")


class ApiUnavailableError(Exception):
    pass


class ApiRequestError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(message)


def _request(path: str, params: dict[str, Any] | None = None) -> Any:
    try:
        resp = requests.get(f"{_BASE_URL}{path}", params=params, timeout=10)
    except (requests.ConnectionError, requests.Timeout) as exc:
        raise ApiUnavailableError("Cannot reach the API.") from exc

    if resp.status_code == 503:
        raise ApiUnavailableError("API reports unavailable.")

    if not resp.ok:
        detail = f"API error {resp.status_code}"
        try:
            body = resp.json()
            if isinstance(body, dict) and "detail" in body:
                detail = str(body["detail"])
        except Exception:
            pass
        raise ApiRequestError(resp.status_code, detail)

    try:
        return resp.json()
    except ValueError as exc:
        raise ApiRequestError(resp.status_code, "API returned invalid JSON.") from exc


def get_health() -> dict[str, Any]:
    return _request("/health")


def get_statistics() -> dict[str, Any]:
    return _request("/statistics")


def search_people(  # noqa: PLR0913
    *,
    id: int | None = None,  # noqa: A002
    passport: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    city: str | None = None,
    address: str | None = None,
    job: str | None = None,
    company: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {}
    if id is not None:
        params["id"] = id
    if passport is not None:
        params["passport"] = passport
    if first_name is not None:
        params["first_name"] = first_name
    if last_name is not None:
        params["last_name"] = last_name
    for name, value in {"city": city, "address": address, "job": job, "company": company}.items():
        if value is not None:
            params[name] = value
    params["limit"] = min(max(limit, 1), 100)
    params["offset"] = max(offset, 0)
    return _request("/people/search", params=params)


def search_by_location_profession(  # noqa: PLR0913
    *,
    city: str | None = None,
    address: str | None = None,
    job: str | None = None,
    company: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {}
    if city is not None:
        params["city"] = city
    if address is not None:
        params["address"] = address
    if job is not None:
        params["job"] = job
    if company is not None:
        params["company"] = company
    params["limit"] = min(max(limit, 1), 100)
    params["offset"] = max(offset, 0)
    return _request("/people/search/by-location-profession", params=params)


def get_person_by_id(person_id: int) -> dict[str, Any] | None:
    rows = search_people(id=person_id, limit=1)
    return rows[0] if rows else None


def search_all(  # noqa: PLR0913
    *,
    id: int | None = None,  # noqa: A002
    passport: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    city: str | None = None,
    address: str | None = None,
    job: str | None = None,
    company: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    return search_people(
        id=id,
        passport=passport,
        first_name=first_name,
        last_name=last_name,
        city=city,
        address=address,
        job=job,
        company=company,
        limit=limit,
        offset=offset,
    )
