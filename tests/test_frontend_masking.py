from __future__ import annotations

from hr_pro_platform.frontend.masking import (
    domain_completeness,
    mask_email,
    mask_ip,
    mask_passport,
    mask_phone,
    mask_tail,
)


class TestMaskTail:
    def test_normal_string(self) -> None:
        assert mask_tail("ABCDEF", 3) == "***DEF"

    def test_short_string(self) -> None:
        assert mask_tail("AB", 3) == "**"

    def test_exact_keep_length(self) -> None:
        assert mask_tail("ABC", 3) == "***"

    def test_empty_string(self) -> None:
        assert mask_tail("", 3) == ""

    def test_whitespace_only(self) -> None:
        assert mask_tail("   ", 3) == ""


class TestMaskPassport:
    def test_normal(self) -> None:
        assert mask_passport("XX12345") == "****345"

    def test_short(self) -> None:
        assert mask_passport("AB") == "**"


class TestMaskPhone:
    def test_normal(self) -> None:
        assert mask_phone("612345678") == "******678"

    def test_short(self) -> None:
        assert mask_phone("12") == "**"


class TestMaskEmail:
    def test_normal(self) -> None:
        assert mask_email("alice@example.com") == "a***@example.com"

    def test_short_local(self) -> None:
        assert mask_email("a@b.com") == "a***@b.com"

    def test_no_at_sign(self) -> None:
        result = mask_email("malformed")
        assert result == "*******ed"

    def test_empty(self) -> None:
        assert mask_email("") == ""


class TestMaskIp:
    def test_normal_ipv4(self) -> None:
        assert mask_ip("84.12.34.56") == "84.12.x.x"

    def test_non_ipv4(self) -> None:
        assert mask_ip("not-an-ip") == "*********"

    def test_three_parts(self) -> None:
        assert mask_ip("1.2.3") == "*****"


class TestDomainCompleteness:
    def test_all_present(self) -> None:
        person: dict[str, object] = {
            "first_name": "Ana",
            "last_name": "García",
            "email": "ana@test.com",
            "telephone_number": "612345678",
            "locations": [{"city": "Madrid"}],
            "professional_profiles": [{"job": "Engineer"}],
        }
        assert domain_completeness(person) == 4

    def test_only_id(self) -> None:
        person: dict[str, object] = {"id": 1}
        assert domain_completeness(person) == 0

    def test_identity_only(self) -> None:
        person: dict[str, object] = {"first_name": "Ana", "last_name": "García"}
        assert domain_completeness(person) == 1

    def test_contact_only(self) -> None:
        person: dict[str, object] = {"email": "a@b.com"}
        assert domain_completeness(person) == 1

    def test_partial(self) -> None:
        person: dict[str, object] = {
            "first_name": "Ana",
            "last_name": "García",
            "locations": [],
            "professional_profiles": [{"job": "Dev"}],
        }
        assert domain_completeness(person) == 2
