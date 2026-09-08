from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from hr_pro_platform.frontend.api_client import (
    ApiRequestError,
    ApiUnavailableError,
    get_health,
    get_person_by_id,
    search_people,
)

MODULE = "hr_pro_platform.frontend.api_client"


def _mock_response(
    status_code: int = 200,
    json_data: object = None,
    text: str = "",
) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.ok = 200 <= status_code < 400
    resp.json.return_value = json_data
    resp.text = text
    return resp


class TestGetHealth:
    @patch(f"{MODULE}.requests.get")
    def test_ok(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_response(200, {"status": "ok"})
        assert get_health() == {"status": "ok"}

    @patch(f"{MODULE}.requests.get")
    def test_connection_error(self, mock_get: MagicMock) -> None:
        import requests as _requests

        mock_get.side_effect = _requests.ConnectionError
        with pytest.raises(ApiUnavailableError):
            get_health()

    @patch(f"{MODULE}.requests.get")
    def test_timeout(self, mock_get: MagicMock) -> None:
        import requests

        mock_get.side_effect = requests.Timeout
        with pytest.raises(ApiUnavailableError):
            get_health()

    @patch(f"{MODULE}.requests.get")
    def test_503(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_response(503, {"status": "unavailable"})
        with pytest.raises(ApiUnavailableError):
            get_health()

    @patch(f"{MODULE}.requests.get")
    def test_invalid_json_is_a_controlled_error(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_response(200)
        mock_get.return_value.json.side_effect = ValueError
        with pytest.raises(ApiRequestError, match="invalid JSON"):
            get_health()


class TestSearchPeople:
    @patch(f"{MODULE}.requests.get")
    def test_builds_url_with_params(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_response(200, [])
        search_people(first_name="Ana", last_name="García", limit=10)
        call_args = mock_get.call_args
        assert "/people/search" in call_args[0][0]
        params = call_args[1]["params"]
        assert params["first_name"] == "Ana"
        assert params["last_name"] == "García"
        assert params["limit"] == 10

    @patch(f"{MODULE}.requests.get")
    def test_400_with_detail(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_response(400, {"detail": "At least one filter required"})
        with pytest.raises(ApiRequestError, match="At least one filter required"):
            search_people()

    @patch(f"{MODULE}.requests.get")
    def test_returns_list(self, mock_get: MagicMock) -> None:
        data = [{"id": 1, "first_name": "Ana"}]
        mock_get.return_value = _mock_response(200, data)
        assert search_people(id=1) == data


class TestGetPersonById:
    @patch(f"{MODULE}.requests.get")
    def test_found(self, mock_get: MagicMock) -> None:
        person = {"id": 5, "first_name": "X"}
        mock_get.return_value = _mock_response(200, [person])
        assert get_person_by_id(5) == person

    @patch(f"{MODULE}.requests.get")
    def test_not_found(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_response(200, [])
        assert get_person_by_id(999) is None


class TestCombinedSearch:
    @patch(f"{MODULE}.requests.get")
    def test_combined_filters_use_one_api_request(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_response(200, [])
        from hr_pro_platform.frontend.api_client import search_all

        search_all(first_name="Ana", city="Madrid", job="Engineer")
        assert mock_get.call_count == 1
        assert mock_get.call_args.kwargs["params"]["city"] == "Madrid"
