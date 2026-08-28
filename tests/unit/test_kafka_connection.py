import pytest

from hr_pro_platform.ingestion.detector import detect_topic


@pytest.mark.parametrize(
    ("fields", "expected"),
    [
        ({"IBAN": "", "passport": "", "salary": ""}, "bank-data"),
        (
            {
                "company": "",
                "company address": "",
                "company_email": "",
                "company_telfnumber": "",
                "fullname": "",
                "job": "",
            },
            "professional-data",
        ),
        ({"address": "", "city": "", "fullname": ""}, "location"),
        (
            {
                "email": "",
                "last_name": "",
                "name": "",
                "passport": "",
                "sex": [],
                "telfnumber": "",
            },
            "personal-data",
        ),
        ({"IPv4": "", "address": ""}, "net-data"),
    ],
)
def test_detect_topic_uses_observed_field_names(fields: dict[str, object], expected: str) -> None:
    assert detect_topic(fields) == expected


def test_detect_topic_returns_none_for_unknown_structure() -> None:
    assert detect_topic({"unknown": ""}) is None
