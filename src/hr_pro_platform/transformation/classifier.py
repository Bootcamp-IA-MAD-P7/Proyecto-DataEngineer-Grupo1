"""Deterministic classification of event fragments by their exact key set."""

from collections.abc import Mapping

UNKNOWN = "unknown"

DOMAIN_FIELDS: dict[str, frozenset[str]] = {
    "Personal": frozenset({"name", "last_name", "sex", "telfnumber", "passport", "email"}),
    "Location": frozenset({"fullname", "city", "address"}),
    "Professional": frozenset(
        {
            "fullname",
            "company",
            "company address",
            "company_telfnumber",
            "company_email",
            "job",
        }
    ),
    "Bank": frozenset({"passport", "IBAN", "salary"}),
    "Net": frozenset({"address", "IPv4"}),
}


def classify_payload(payload: Mapping[str, object]) -> str:
    """Return the domain whose required key set exactly matches ``payload``.

    Values are intentionally ignored. Unsupported key sets return ``unknown``.
    The input mapping is only read and is never mutated.
    """

    payload_fields = frozenset(payload)
    for domain, required_fields in DOMAIN_FIELDS.items():
        if payload_fields == required_fields:
            return domain
    return UNKNOWN
