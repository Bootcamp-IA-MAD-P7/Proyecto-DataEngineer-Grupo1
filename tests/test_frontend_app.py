"""Streamlit AppTest coverage for the user-visible frontend flows."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

streamlit = pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = Path(__file__).resolve().parents[1] / "src/hr_pro_platform/frontend/app.py"
HEALTH = {"status": "ok"}
STATS = {
    "rows_per_table": {"employees": 1, "locations": 1, "professional_profiles": 1},
    "employees_missing_domain": {},
}
PERSON = {
    "id": 1,
    "first_name": "Ana",
    "last_name": "Gomez",
    "passport": "P-123456",
    "email": "ana@example.test",
    "telephone_number": "600000000",
    "sex": ["F"],
    "locations": [],
    "professional_profiles": [],
}


def _app() -> AppTest:
    return AppTest.from_file(APP, default_timeout=10)


def _response(payload: object) -> MagicMock:
    response = MagicMock(ok=True, status_code=200)
    response.json.return_value = payload
    return response


def test_app_startup_and_statistics() -> None:
    with patch(
        "hr_pro_platform.frontend.api_client.requests.get",
        side_effect=[_response(HEALTH), _response(STATS)],
    ):
        at = _app().run()
    assert not at.exception
    assert at.success[0].value == "API available"
    assert any(metric.label == "Employees" for metric in at.metric)


def test_search_results_and_detail_are_masked() -> None:
    def request(url: str, **_: object) -> MagicMock:
        if url.endswith("/health"):
            return _response(HEALTH)
        if url.endswith("/statistics"):
            return _response(STATS)
        return _response([PERSON])

    with patch("hr_pro_platform.frontend.api_client.requests.get", side_effect=request):
        at = _app().run()
        at.text_input(key="s_first_name").set_value("Ana")
        at.button[0].click().run()
    assert not at.exception
    assert "P-123456" not in " ".join(str(x.value) for x in at.json)


def test_api_unavailable_is_user_facing_error() -> None:
    with patch(
        "hr_pro_platform.frontend.api_client.requests.get", side_effect=requests.ConnectionError
    ):
        at = _app().run()
    assert not at.exception
    assert any("API unavailable" in warning.value for warning in at.warning)
