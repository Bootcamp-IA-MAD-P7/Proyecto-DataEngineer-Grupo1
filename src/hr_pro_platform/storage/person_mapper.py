"""Pure mapping from ``ConsolidatedPersonRecord`` to PostgreSQL candidate rows.

See docs/specs/HRP-55-etl-postgres-connection.md. This module performs no
database I/O and assigns no primary key: it only translates the transformation
layer's output into the column shape already created by HRP-54
(``storage/postgres.py``), reusing the observed-field-to-column mapping
approved in ``docs/specs/HRP-25-modelo-datos.md``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from ..transformation.fragment_contract import JSONValue, SourceReference
from ..transformation.person_consolidator import ConsolidatedPersonRecord, DomainName

EMPLOYEES: Final = "employees"
LOCATIONS: Final = "locations"
PROFESSIONAL_PROFILES: Final = "professional_profiles"
BANK_ACCOUNTS: Final = "bank_accounts"
NETWORK_DATA: Final = "network_data"

# Observed field -> curated column, per domain. Sourced from
# docs/specs/HRP-25-modelo-datos.md; this module does not redefine it.
_FIELD_MAP: dict[DomainName, dict[str, str]] = {
    "personal": {
        "name": "first_name",
        "last_name": "last_name",
        "sex": "sex",
        "telfnumber": "telephone_number",
        "email": "email",
        "passport": "passport",
    },
    "location": {
        "fullname": "full_name",
        "city": "city",
        "address": "address",
        "IPv4": "ip_v4",
    },
    "professional": {
        "fullname": "full_name",
        "company": "company",
        "company address": "company_address",
        "company_email": "company_email",
        "company_telfnumber": "company_telephone_number",
        "job": "job",
    },
    "bank": {
        "IBAN": "iban",
        "passport": "passport",
        "salary": "salary",
    },
    "net": {
        "IPv4": "ip_v4",
    },
}

_TABLE_BY_DOMAIN: dict[DomainName, str] = {
    "personal": EMPLOYEES,
    "location": LOCATIONS,
    "professional": PROFESSIONAL_PROFILES,
    "bank": BANK_ACCOUNTS,
    "net": NETWORK_DATA,
}


@dataclass(frozen=True)
class CandidateRow:
    """One candidate row for a curated table.

    Carries no primary key and no ``employee_id``: assigning or resolving
    those is explicitly out of scope for this task (see the spec's "What
    stays open" section) and belongs to HRP-56.
    """

    table: str
    group_key: str
    fields: Mapping[str, JSONValue]
    source_reference: SourceReference


@dataclass(frozen=True)
class PersonRecordMapping:
    """Candidate rows produced from one ``ConsolidatedPersonRecord``."""

    status: str
    correlation_rules: tuple[str, ...]
    provenance: tuple[SourceReference, ...]
    employees: tuple[CandidateRow, ...]
    locations: tuple[CandidateRow, ...]
    professional_profiles: tuple[CandidateRow, ...]
    bank_accounts: tuple[CandidateRow, ...]
    network_data: tuple[CandidateRow, ...]


def map_person_record(record: ConsolidatedPersonRecord) -> PersonRecordMapping:
    """Translate one consolidated record into per-table candidate rows.

    One candidate row is produced per retained ``GroupedFragment`` (not per
    group and not per domain): a local group holding more than one fragment
    (an intra-group ambiguity) or a domain holding more than one group (a
    cross-group ambiguity, per HRP-96) both surface as multiple candidate
    rows sharing the same ``group_key`` where applicable, instead of being
    silently merged into one fabricated row.
    """

    rows_by_domain: dict[DomainName, tuple[CandidateRow, ...]] = {}
    for domain, contribution in record.domains.items():
        if contribution is None:
            rows_by_domain[domain] = ()
            continue
        table = _TABLE_BY_DOMAIN[domain]
        field_map = _FIELD_MAP[domain]
        rows_by_domain[domain] = tuple(
            CandidateRow(
                table=table,
                group_key=group.key,
                fields={
                    column: fragment.payload[observed_field]
                    for observed_field, column in field_map.items()
                    if observed_field in fragment.payload
                },
                source_reference=fragment.source_reference,
            )
            for group in contribution.groups
            for fragment in group.fragments
        )

    return PersonRecordMapping(
        status=record.status,
        correlation_rules=record.correlation_rules,
        provenance=record.provenance,
        employees=rows_by_domain["personal"],
        locations=rows_by_domain["location"],
        professional_profiles=rows_by_domain["professional"],
        bank_accounts=rows_by_domain["bank"],
        network_data=rows_by_domain["net"],
    )
