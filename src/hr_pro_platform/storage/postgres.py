from __future__ import annotations

from typing import Any

import psycopg

from ..ingestion.error_handler import get_logger
from .config import POSTGRES_DB, POSTGRES_HOST, POSTGRES_PASSWORD, POSTGRES_PORT, POSTGRES_USER

logger = get_logger("postgres")

# Candidate schema from docs/specs/HRP-52-tablas-relaciones.md. No column is
# NOT NULL beyond a table's own primary key, its FK-to-employees ownership link
# (nullable only on processing_audit, per HRP-52) and audit timestamps: required,
# optional and nullable business rules remain pending per docs/02-data-contract.md.
#
# `sex` (observed as a JSON array) is stored as JSONB and `salary`/`ip_v4`
# (observed as strings, format unconfirmed) are stored as TEXT: this preserves the
# observed shape without inventing a business format, per ADR-0003.
_SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS employees (
        id BIGSERIAL PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        sex JSONB,
        telephone_number TEXT,
        email TEXT,
        passport TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS locations (
        id BIGSERIAL PRIMARY KEY,
        employee_id BIGINT NOT NULL,
        full_name TEXT,
        city TEXT,
        address TEXT,
        ip_v4 TEXT,
        CONSTRAINT fk_locations_employees FOREIGN KEY (employee_id)
            REFERENCES employees (id) ON DELETE CASCADE
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_locations_employee_id ON locations (employee_id)",
    """
    CREATE TABLE IF NOT EXISTS professional_profiles (
        id BIGSERIAL PRIMARY KEY,
        employee_id BIGINT NOT NULL,
        full_name TEXT,
        company TEXT,
        company_address TEXT,
        company_email TEXT,
        company_telephone_number TEXT,
        job TEXT,
        CONSTRAINT fk_professional_profiles_employees FOREIGN KEY (employee_id)
            REFERENCES employees (id) ON DELETE CASCADE
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_professional_profiles_employee_id "
    "ON professional_profiles (employee_id)",
    """
    CREATE TABLE IF NOT EXISTS bank_accounts (
        id BIGSERIAL PRIMARY KEY,
        employee_id BIGINT NOT NULL,
        iban TEXT,
        passport TEXT,
        salary TEXT,
        CONSTRAINT fk_bank_accounts_employees FOREIGN KEY (employee_id)
            REFERENCES employees (id) ON DELETE CASCADE
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_bank_accounts_employee_id ON bank_accounts (employee_id)",
    """
    CREATE TABLE IF NOT EXISTS network_data (
        id BIGSERIAL PRIMARY KEY,
        employee_id BIGINT NOT NULL,
        ip_v4 TEXT,
        CONSTRAINT fk_network_data_employees FOREIGN KEY (employee_id)
            REFERENCES employees (id) ON DELETE CASCADE
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_network_data_employee_id ON network_data (employee_id)",
    """
    CREATE TABLE IF NOT EXISTS processing_audit (
        id BIGSERIAL PRIMARY KEY,
        employee_id BIGINT,
        stage TEXT,
        status TEXT,
        raw_event_ref TEXT,
        occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT fk_processing_audit_employees FOREIGN KEY (employee_id)
            REFERENCES employees (id) ON DELETE SET NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_processing_audit_employee_id ON processing_audit (employee_id)",
    "CREATE INDEX IF NOT EXISTS ix_processing_audit_occurred_at ON processing_audit (occurred_at)",
)


class PostgresSchemaClient:
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

    def create_schema(self) -> None:
        assert self._connection is not None
        with self._connection.cursor() as cursor:
            for statement in _SCHEMA_STATEMENTS:
                cursor.execute(statement)
        self._connection.commit()
        logger.info("PostgreSQL schema ensured (%d statements)", len(_SCHEMA_STATEMENTS))

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            logger.info("PostgreSQL connection closed")
