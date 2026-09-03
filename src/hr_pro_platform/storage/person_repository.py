"""Insert HRP-55 ``PersonRecordMapping`` output into PostgreSQL.

See docs/specs/HRP-56-insert-processed-person-records.md,
docs/specs/HRP-58-avoid-duplicate-records.md and
docs/specs/HRP-57-update-records-on-new-data.md. Only components whose
``employees`` tuple has exactly one candidate row are inserted; a component
with zero or more than one candidate ``employees`` row is skipped explicitly
rather than guessing an association (see HRP-56's "Design" section). A
component whose employee candidate row's ``source_reference`` was already
recorded in ``processing_audit`` (HRP-58) no longer skips unconditionally:
any dependent-table candidate row not already present for that existing
``employee_id`` is inserted as an enrichment (HRP-57) — an exact-match
technical check, not person-identity deduplication or resolution; no
business-identity field is used. ``employees``' own columns are never
updated by this module.
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
    """Result of attempting to insert one ``PersonRecordMapping``.

    ``enriched_tables`` (HRP-57) lists the dependent tables that received a
    genuinely new row for an already-existing ``employee_id`` on this call.
    Empty for a fresh ``employees`` insert (``inserted=True``) and for a
    component with nothing new to add (``skipped_reason="already_processed"``,
    unchanged from HRP-58). Non-empty only when ``inserted=False`` and
    ``skipped_reason=None`` -- HRP-57's enrichment outcome.
    """

    inserted: bool
    employee_id: int | None
    skipped_reason: str | None
    enriched_tables: tuple[str, ...] = ()


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
                # already-processed fragment -- see that spec's "Risks" for
                # why a database-level unique index remains a separate,
                # explicitly pending proposal rather than being assumed here.
                if self._already_processed(cursor, source_reference):
                    # HRP-57: an already-recorded source_reference no longer
                    # skips unconditionally -- genuinely new dependent rows
                    # for the existing employee_id are still inserted. This
                    # never touches employees' own columns and never queries
                    # or compares a business-identity field. When there are
                    # no dependent rows to consider, this is a pure replay
                    # and behaves exactly as HRP-58 originally did (a single
                    # check, no further lookup).
                    enriched_tables: tuple[str, ...] = ()
                    existing_employee_id: int | None = None
                    if dependent_rows:
                        existing_employee_id = self._find_existing_employee_id(
                            cursor, source_reference
                        )
                        assert existing_employee_id is not None
                        enriched_tables = self._enrich_existing_employee(
                            cursor, existing_employee_id, dependent_rows
                        )
                    if enriched_tables:
                        assert existing_employee_id is not None
                        self._record_processing_audit_update(
                            cursor, existing_employee_id, source_reference
                        )
                    self._connection.commit()
                    if enriched_tables:
                        logger.info(
                            "Enriched existing component | employee_id=%s "
                            "source_reference=%s enriched_tables=%s",
                            existing_employee_id,
                            source_reference,
                            ",".join(enriched_tables),
                        )
                        return InsertOutcome(
                            inserted=False,
                            employee_id=existing_employee_id,
                            skipped_reason=None,
                            enriched_tables=enriched_tables,
                        )
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

    # -- HRP-57: enrichment of an already-processed component -----------------
    # These four helpers are additive to HRP-58's approved _already_processed()
    # and _record_processing_audit(), which are left completely unchanged.

    @staticmethod
    def _find_existing_employee_id(
        cursor: psycopg.Cursor[Any], source_reference: str
    ) -> int | None:
        """Resolve the employee_id already recorded for this source_reference.

        Reads processing_audit only -- never a business-identity field.
        """

        cursor.execute(
            "SELECT employee_id FROM processing_audit "
            "WHERE raw_event_ref = %s AND employee_id IS NOT NULL "
            "ORDER BY occurred_at LIMIT 1",
            [source_reference],
        )
        result = cursor.fetchone()
        return int(result[0]) if result is not None else None

    @staticmethod
    def _dependent_row_exists(
        cursor: psycopg.Cursor[Any], table: str, employee_id: int, row: CandidateRow
    ) -> bool:
        """Exact-match check: does an identical row already exist for this
        employee_id in this table? No fuzzy or partial comparison."""

        columns = list(row.fields.keys())
        conditions = [sql.SQL("employee_id = {}").format(sql.Placeholder())]
        conditions += [
            sql.SQL("{column} = {placeholder}").format(
                column=sql.Identifier(column), placeholder=sql.Placeholder()
            )
            for column in columns
        ]
        query = sql.SQL("SELECT 1 FROM {table} WHERE {conditions} LIMIT 1").format(
            table=sql.Identifier(table),
            conditions=sql.SQL(" AND ").join(conditions),
        )
        values = [employee_id, *(_bind_value(column, row.fields[column]) for column in columns)]
        cursor.execute(query, values)
        return cursor.fetchone() is not None

    def _enrich_existing_employee(
        self,
        cursor: psycopg.Cursor[Any],
        employee_id: int,
        dependent_rows: tuple[tuple[str, CandidateRow], ...],
    ) -> tuple[str, ...]:
        """Insert only the dependent rows not already present for employee_id.

        Never updates or deletes an existing row; never touches employees'
        own columns.
        """

        enriched_tables: list[str] = []
        for table, row in dependent_rows:
            if self._dependent_row_exists(cursor, table, employee_id, row):
                continue
            self._insert_dependent(cursor, table, row, employee_id)
            enriched_tables.append(table)
        return tuple(enriched_tables)

    @staticmethod
    def _record_processing_audit_update(
        cursor: psycopg.Cursor[Any], employee_id: int, source_reference: str
    ) -> None:
        """Mark the existing processing_audit row as enriched.

        HRP-58's proposed unique index (ix_processing_audit_raw_event_ref)
        allows at most one row per raw_event_ref, so this cannot INSERT a
        second row for the same source_reference -- it UPDATEs stage/status
        on the row HRP-58's _record_processing_audit() already wrote. This
        is bookkeeping on the audit table itself, not a business decision:
        it never touches employees or any dependent table's columns.
        """

        cursor.execute(
            "UPDATE processing_audit SET stage = %s, status = %s, occurred_at = now() "
            "WHERE employee_id = %s AND raw_event_ref = %s",
            ["update", "enriched", employee_id, source_reference],
        )
