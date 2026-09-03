"""Insert HRP-55 ``PersonRecordMapping`` output into PostgreSQL.

See docs/specs/HRP-56-insert-processed-person-records.md and
docs/specs/HRP-58-avoid-duplicate-records.md. Only components whose
``employees`` tuple has exactly one candidate row are inserted; a component
with zero or more than one candidate ``employees`` row is skipped explicitly
rather than guessing an association (see HRP-56's "Design" section). A
component whose employee candidate row's ``source_reference`` was already
recorded in ``processing_audit`` is skipped as an already-processed
reinsertion (HRP-58) — this is source-reprocessing idempotency, not
person-identity deduplication; no business-identity field is used. No
``UPDATE`` behaviour is introduced here — that is HRP-57.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

from ..ingestion.error_handler import get_logger
from .config import POSTGRES_DB, POSTGRES_HOST, POSTGRES_PASSWORD, POSTGRES_PORT, POSTGRES_USER
from .person_mapper import CandidateRow, PersonRecordMapping

logger = get_logger("person_repository")

# employees.sex is the only JSONB column any CandidateRow can populate
# (see storage/postgres.py's _SCHEMA_STATEMENTS); psycopg does not infer
# JSONB from a plain Python list, so it must be adapted explicitly.
_JSONB_COLUMNS: frozenset[str] = frozenset({"sex"})


def _bind_value(column: str, value: object) -> object:
    return Jsonb(value) if column in _JSONB_COLUMNS else value


@dataclass(frozen=True)
class InsertOutcome:
    """Result of attempting to insert one ``PersonRecordMapping``."""

    inserted: bool
    employee_id: int | None
    skipped_reason: str | None


class PersonRepository:
    """Inserts ``PersonRecordMapping`` candidate rows into PostgreSQL."""

    def __init__(self) -> None:
        self._connection: psycopg.Connection[Any] | None = None

    def connect(self) -> None:
        self._connection = psycopg.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
        )
        self._connection.execute("SELECT 1")
        logger.info("Connected to PostgreSQL | db=%s host=%s", POSTGRES_DB, POSTGRES_HOST)

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            logger.info("PostgreSQL connection closed")

    def insert_mapping(self, mapping: PersonRecordMapping) -> InsertOutcome:
        """Insert one component's candidate rows, or skip it explicitly."""

        assert self._connection is not None

        if len(mapping.employees) == 0:
            logger.info("Skipping component | reason=no_personal_domain")
            return InsertOutcome(
                inserted=False, employee_id=None, skipped_reason="no_personal_domain"
            )
        if len(mapping.employees) > 1:
            logger.info(
                "Skipping component | reason=ambiguous_personal_domain candidate_rows=%d",
                len(mapping.employees),
            )
            return InsertOutcome(
                inserted=False, employee_id=None, skipped_reason="ambiguous_personal_domain"
            )

        dependent_rows: tuple[tuple[str, CandidateRow], ...] = tuple(
            (table, row)
            for table, rows in (
                ("locations", mapping.locations),
                ("professional_profiles", mapping.professional_profiles),
                ("bank_accounts", mapping.bank_accounts),
                ("network_data", mapping.network_data),
            )
            for row in rows
        )
        source_reference = mapping.employees[0].source_reference

        try:
            with self._connection.cursor() as cursor:
                # HRP-58: check-then-insert within the same transaction as the
                # write it guards. This narrows, but does not eliminate, the
                # race between two concurrent writers reinserting the same
                # already-processed fragment -- see the spec's "Risks" for
                # why a database-level unique index remains a separate,
                # explicitly pending proposal rather than being assumed here.
                if self._already_processed(cursor, source_reference):
                    self._connection.commit()
                    logger.info(
                        "Skipping component | reason=already_processed source_reference=%s",
                        source_reference,
                    )
                    return InsertOutcome(
                        inserted=False, employee_id=None, skipped_reason="already_processed"
                    )
                employee_id = self._insert_employee(cursor, mapping.employees[0])
                for table, row in dependent_rows:
                    self._insert_dependent(cursor, table, row, employee_id)
                self._record_processing_audit(cursor, employee_id, source_reference)
            self._connection.commit()
        except Exception as error:
            self._connection.rollback()
            # Log only allowlisted, non-sensitive metadata: a database error's
            # message/DETAIL can echo rejected values, per docs/backend-standards.md
            # ("Must not: Log sensitive payloads").
            sqlstate = getattr(error, "sqlstate", None)
            logger.error(
                "Component insert failed; transaction rolled back | error_class=%s sqlstate=%s",
                type(error).__name__,
                sqlstate,
            )
            raise

        logger.info(
            "Inserted component | employee_id=%s dependent_rows=%d",
            employee_id,
            len(dependent_rows),
        )
        return InsertOutcome(inserted=True, employee_id=employee_id, skipped_reason=None)

    def insert_mappings(self, mappings: Iterable[PersonRecordMapping]) -> list[InsertOutcome]:
        """Insert each mapping, isolating a failure to its own component."""

        outcomes: list[InsertOutcome] = []
        for mapping in mappings:
            try:
                outcomes.append(self.insert_mapping(mapping))
            except Exception:
                # insert_mapping() already rolled back and logged the failure;
                # record the outcome here and continue with the next component.
                outcomes.append(
                    InsertOutcome(inserted=False, employee_id=None, skipped_reason="insert_error")
                )
        return outcomes

    @staticmethod
    def _already_processed(cursor: psycopg.Cursor[Any], source_reference: str) -> bool:
        """Check processing_audit for a prior insert of this exact source event.

        This is source-reprocessing idempotency (HRP-58), not person-identity
        deduplication: it only asks "have I already inserted this fragment?",
        never "is this the same real person as an existing row?".
        """

        cursor.execute(
            "SELECT 1 FROM processing_audit WHERE raw_event_ref = %s LIMIT 1",
            [source_reference],
        )
        return cursor.fetchone() is not None

    @staticmethod
    def _record_processing_audit(
        cursor: psycopg.Cursor[Any], employee_id: int, source_reference: str
    ) -> None:
        cursor.execute(
            "INSERT INTO processing_audit (employee_id, stage, status, raw_event_ref) "
            "VALUES (%s, %s, %s, %s)",
            [employee_id, "insert", "inserted", source_reference],
        )

    @staticmethod
    def _insert_employee(cursor: psycopg.Cursor[Any], row: CandidateRow) -> int:
        columns = list(row.fields.keys())
        query = sql.SQL("INSERT INTO employees ({fields}) VALUES ({values}) RETURNING id").format(
            fields=sql.SQL(", ").join(sql.Identifier(column) for column in columns),
            values=sql.SQL(", ").join(sql.Placeholder() for _ in columns),
        )
        cursor.execute(query, [_bind_value(column, row.fields[column]) for column in columns])
        result = cursor.fetchone()
        assert result is not None
        return int(result[0])

    @staticmethod
    def _insert_dependent(
        cursor: psycopg.Cursor[Any], table: str, row: CandidateRow, employee_id: int
    ) -> None:
        columns = ["employee_id", *row.fields.keys()]
        query = sql.SQL("INSERT INTO {table} ({fields}) VALUES ({values})").format(
            table=sql.Identifier(table),
            fields=sql.SQL(", ").join(sql.Identifier(column) for column in columns),
            values=sql.SQL(", ").join(sql.Placeholder() for _ in columns),
        )
        values = [employee_id, *(_bind_value(column, row.fields[column]) for column in row.fields)]
        cursor.execute(query, values)
