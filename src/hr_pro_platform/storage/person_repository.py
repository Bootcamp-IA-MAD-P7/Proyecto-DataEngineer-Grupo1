"""Insert HRP-55 ``PersonRecordMapping`` output into PostgreSQL.

See docs/specs/HRP-56-insert-processed-person-records.md. Only components
whose ``employees`` tuple has exactly one candidate row are inserted; a
component with zero or more than one candidate ``employees`` row is skipped
explicitly rather than guessing an association (see the spec's "Design"
section). No ``UPDATE``, deduplication or ``ON CONFLICT`` behaviour is
introduced here — that is HRP-57/HRP-58.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import psycopg
from psycopg import sql

from ..ingestion.error_handler import get_logger
from .config import POSTGRES_DB, POSTGRES_HOST, POSTGRES_PASSWORD, POSTGRES_PORT, POSTGRES_USER
from .person_mapper import CandidateRow, PersonRecordMapping

logger = get_logger("person_repository")


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

        try:
            with self._connection.cursor() as cursor:
                employee_id = self._insert_employee(cursor, mapping.employees[0])
                for table, row in dependent_rows:
                    self._insert_dependent(cursor, table, row, employee_id)
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            logger.exception("Component insert failed; transaction rolled back")
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
    def _insert_employee(cursor: psycopg.Cursor[Any], row: CandidateRow) -> int:
        columns = list(row.fields.keys())
        query = sql.SQL("INSERT INTO employees ({fields}) VALUES ({values}) RETURNING id").format(
            fields=sql.SQL(", ").join(sql.Identifier(column) for column in columns),
            values=sql.SQL(", ").join(sql.Placeholder() for _ in columns),
        )
        cursor.execute(query, [row.fields[column] for column in columns])
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
        cursor.execute(query, [employee_id, *row.fields.values()])
