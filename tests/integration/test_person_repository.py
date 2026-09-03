"""HRP-56 integration test: real insert against the HRP-53 PostgreSQL container.

Reuses the `live_connection` skip pattern from `test_postgres_schema.py`: this
test is skipped automatically whenever PostgreSQL is not reachable, matching
CI's current lack of a live Docker service.
"""

from __future__ import annotations

from collections.abc import Iterator

import psycopg
import pytest


@pytest.fixture
def live_connection() -> Iterator[psycopg.Connection[tuple[object, ...]]]:
    try:
        from hr_pro_platform.storage.config import (
            POSTGRES_DB,
            POSTGRES_HOST,
            POSTGRES_PASSWORD,
            POSTGRES_PORT,
            POSTGRES_USER,
        )
    except OSError:
        pytest.skip("PostgreSQL environment variables are not configured (.env missing?).")

    try:
        connection = psycopg.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            connect_timeout=2,
        )
    except psycopg.OperationalError:
        pytest.skip(
            "PostgreSQL is not reachable; "
            "start it with `docker compose -f infra/compose.dev.yml up -d postgres`."
        )
    try:
        yield connection
    finally:
        connection.close()


def test_insert_mapping_round_trips_through_a_real_database(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    from hr_pro_platform.storage.person_mapper import CandidateRow, PersonRecordMapping
    from hr_pro_platform.storage.person_repository import InsertOutcome, PersonRepository
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    schema_client = PostgresSchemaClient()
    schema_client.connect()
    try:
        schema_client.create_schema()
    finally:
        schema_client.close()

    mapping = PersonRecordMapping(
        status="complete",
        correlation_rules=("personal_bank_passport",),
        provenance=("integration-test-source",),
        employees=(
            CandidateRow(
                table="employees",
                group_key="INTEGRATION-TEST-P-001",
                fields={
                    "first_name": "IntegrationTest",
                    "last_name": "Fixture",
                    "sex": ["X"],
                    "passport": "INTEGRATION-TEST-P-001",
                },
                source_reference="integration-test-source",
            ),
        ),
        locations=(
            CandidateRow(
                table="locations",
                group_key="IntegrationTest Fixture",
                fields={"full_name": "IntegrationTest Fixture", "city": "Springfield"},
                source_reference="integration-test-source",
            ),
        ),
        professional_profiles=(),
        bank_accounts=(),
        network_data=(),
    )

    repository = PersonRepository()
    repository.connect()
    outcome: InsertOutcome | None = None
    try:
        outcome = repository.insert_mapping(mapping)

        assert outcome.inserted is True
        assert outcome.employee_id is not None

        with live_connection.cursor() as cursor:
            cursor.execute(
                "SELECT first_name, passport, sex FROM employees WHERE id = %s",
                (outcome.employee_id,),
            )
            employee_row = cursor.fetchone()
            cursor.execute(
                "SELECT full_name, employee_id FROM locations WHERE employee_id = %s",
                (outcome.employee_id,),
            )
            location_row = cursor.fetchone()

        assert employee_row == ("IntegrationTest", "INTEGRATION-TEST-P-001", ["X"])
        assert location_row == ("IntegrationTest Fixture", outcome.employee_id)
    finally:
        try:
            if outcome is not None and outcome.employee_id is not None:
                # Scoped to exactly the employee row this test created, not a
                # fixed reference/predicate that could match a row this
                # execution did not create. processing_audit is deleted
                # first, by employee_id, before the employees row itself --
                # deleting employees first would null out employee_id
                # (ON DELETE SET NULL) and make this scoping impossible.
                with live_connection.cursor() as cleanup_cursor:
                    cleanup_cursor.execute(
                        "DELETE FROM processing_audit WHERE employee_id = %s",
                        (outcome.employee_id,),
                    )
                    cleanup_cursor.execute(
                        "DELETE FROM employees WHERE id = %s", (outcome.employee_id,)
                    )
                live_connection.commit()
        finally:
            repository.close()


def test_reprocessing_the_same_source_reference_inserts_once_and_skips_the_second_time(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    from hr_pro_platform.storage.person_mapper import CandidateRow, PersonRecordMapping
    from hr_pro_platform.storage.person_repository import InsertOutcome, PersonRepository
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    schema_client = PostgresSchemaClient()
    schema_client.connect()
    try:
        schema_client.create_schema()
    finally:
        schema_client.close()

    mapping = PersonRecordMapping(
        status="complete",
        correlation_rules=(),
        provenance=("integration-test-dedup-source",),
        employees=(
            CandidateRow(
                table="employees",
                group_key="INTEGRATION-TEST-P-DEDUP",
                fields={
                    "first_name": "DedupTest",
                    "last_name": "Fixture",
                    "passport": "INTEGRATION-TEST-P-DEDUP",
                },
                source_reference="integration-test-dedup-source",
            ),
        ),
        locations=(),
        professional_profiles=(),
        bank_accounts=(),
        network_data=(),
    )

    repository = PersonRepository()
    repository.connect()
    first_outcome: InsertOutcome | None = None
    second_outcome: InsertOutcome | None = None
    try:
        first_outcome = repository.insert_mapping(mapping)
        second_outcome = repository.insert_mapping(mapping)

        assert first_outcome.inserted is True
        assert second_outcome.inserted is False
        assert second_outcome.skipped_reason == "already_processed"
        assert second_outcome.employee_id is None

        with live_connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM employees WHERE passport = %s",
                ("INTEGRATION-TEST-P-DEDUP",),
            )
            employee_count = cursor.fetchone()
            cursor.execute(
                "SELECT count(*) FROM processing_audit WHERE raw_event_ref = %s",
                ("integration-test-dedup-source",),
            )
            audit_count = cursor.fetchone()

        assert employee_count == (1,)  # not duplicated by the second attempt
        assert audit_count == (1,)  # not duplicated either
    finally:
        try:
            if first_outcome is not None and first_outcome.employee_id is not None:
                # Scoped to the employee_id this run created (audit deleted
                # first, by employee_id, before the employees row), not to
                # the fixed source_reference string -- a fixed-string delete
                # would remove an audit row this run did not create if one
                # already existed under that exact reference.
                with live_connection.cursor() as cleanup_cursor:
                    cleanup_cursor.execute(
                        "DELETE FROM processing_audit WHERE employee_id = %s",
                        (first_outcome.employee_id,),
                    )
                    cleanup_cursor.execute(
                        "DELETE FROM employees WHERE id = %s", (first_outcome.employee_id,)
                    )
                live_connection.commit()
        finally:
            repository.close()


def test_two_distinct_source_references_both_insert_and_only_the_replay_skips(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    """Real-database proof that the idempotency check filters by the exact
    requested source_reference, not by "any row exists". A mock cannot prove
    this -- it only simulates application logic, not actual SQL filtering
    (see the equivalent, mock-only test in tests/unit/test_person_repository.py
    for why this scenario needs a live database to be meaningful).
    """
    from hr_pro_platform.storage.person_mapper import CandidateRow, PersonRecordMapping
    from hr_pro_platform.storage.person_repository import InsertOutcome, PersonRepository
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    schema_client = PostgresSchemaClient()
    schema_client.connect()
    try:
        schema_client.create_schema()
    finally:
        schema_client.close()

    shared_passport = "INTEGRATION-TEST-P-REF-SHARED"

    def build_mapping(source_reference: str) -> PersonRecordMapping:
        # Deliberately identical business fields across A and B (same
        # passport, same name) -- only source_reference differs, so a
        # lookup that ignores the requested reference (e.g.
        # "SELECT 1 FROM processing_audit LIMIT 1") would incorrectly
        # report B as already processed once A is inserted. Nothing in the
        # employees schema enforces passport uniqueness, so two rows with
        # the same passport are a valid, expected outcome here.
        return PersonRecordMapping(
            status="complete",
            correlation_rules=(),
            provenance=(source_reference,),
            employees=(
                CandidateRow(
                    table="employees",
                    group_key=shared_passport,
                    fields={
                        "first_name": "TwoRefTest",
                        "last_name": "Fixture",
                        "passport": shared_passport,
                    },
                    source_reference=source_reference,
                ),
            ),
            locations=(),
            professional_profiles=(),
            bank_accounts=(),
            network_data=(),
        )

    mapping_a = build_mapping("integration-test-source-A")
    mapping_b = build_mapping("integration-test-source-B")

    repository = PersonRepository()
    repository.connect()
    outcome_a: InsertOutcome | None = None
    outcome_b: InsertOutcome | None = None
    try:
        outcome_a = repository.insert_mapping(mapping_a)
        outcome_b = repository.insert_mapping(mapping_b)
        replay_a = repository.insert_mapping(mapping_a)
        replay_b = repository.insert_mapping(mapping_b)

        assert outcome_a.inserted is True
        assert outcome_b.inserted is True
        assert replay_a.inserted is False
        assert replay_a.skipped_reason == "already_processed"
        assert replay_b.inserted is False
        assert replay_b.skipped_reason == "already_processed"

        created_employee_ids = [
            outcome.employee_id
            for outcome in (outcome_a, outcome_b)
            if outcome is not None and outcome.employee_id is not None
        ]

        with live_connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM employees WHERE id = ANY(%s)",
                (created_employee_ids,),
            )
            employee_count = cursor.fetchone()

        assert employee_count == (2,)  # one per reference, no cross-reference skip
    finally:
        try:
            # Scoped to exactly the employee_id values this run created, not
            # to the fixed source_reference strings -- deleting by a fixed
            # reference could remove an audit row this run did not create.
            # Delete processing_audit (by employee_id) before employees.
            with live_connection.cursor() as cleanup_cursor:
                created_employee_ids = [
                    outcome.employee_id
                    for outcome in (outcome_a, outcome_b)
                    if outcome is not None and outcome.employee_id is not None
                ]
                if created_employee_ids:
                    cleanup_cursor.execute(
                        "DELETE FROM processing_audit WHERE employee_id = ANY(%s)",
                        (created_employee_ids,),
                    )
                    cleanup_cursor.execute(
                        "DELETE FROM employees WHERE id = ANY(%s)",
                        (created_employee_ids,),
                    )
            live_connection.commit()
        finally:
            repository.close()


def test_skipping_a_pre_existing_reference_leaves_its_audit_record_untouched(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    """Regression test for a cleanup bug: deleting processing_audit rows by
    a fixed source_reference string (instead of by the employee_id this
    test run actually created) could remove an audit record that already
    existed before this test ran. This seeds that pre-existing state
    directly, confirms insert_mapping() skips it without touching it, and
    proves the record is still there afterward.
    """
    from hr_pro_platform.storage.person_mapper import CandidateRow, PersonRecordMapping
    from hr_pro_platform.storage.person_repository import PersonRepository
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    schema_client = PostgresSchemaClient()
    schema_client.connect()
    try:
        schema_client.create_schema()
    finally:
        schema_client.close()

    pre_existing_reference = "integration-test-pre-existing-source"
    pre_existing_employee_id: int | None = None

    # Seed state this test run did not create, bypassing PersonRepository.
    with live_connection.cursor() as seed_cursor:
        seed_cursor.execute(
            "INSERT INTO employees (first_name, last_name, passport) "
            "VALUES (%s, %s, %s) RETURNING id",
            ("PreExisting", "Fixture", "INTEGRATION-TEST-P-PREEXISTING"),
        )
        result = seed_cursor.fetchone()
        assert result is not None
        pre_existing_employee_id = result[0]
        seed_cursor.execute(
            "INSERT INTO processing_audit (employee_id, stage, status, raw_event_ref) "
            "VALUES (%s, %s, %s, %s)",
            (pre_existing_employee_id, "insert", "inserted", pre_existing_reference),
        )
    live_connection.commit()

    mapping = PersonRecordMapping(
        status="complete",
        correlation_rules=(),
        provenance=(pre_existing_reference,),
        employees=(
            CandidateRow(
                table="employees",
                group_key="INTEGRATION-TEST-P-PREEXISTING",
                fields={
                    "first_name": "PreExisting",
                    "last_name": "Fixture",
                    "passport": "INTEGRATION-TEST-P-PREEXISTING",
                },
                source_reference=pre_existing_reference,
            ),
        ),
        locations=(),
        professional_profiles=(),
        bank_accounts=(),
        network_data=(),
    )

    repository = PersonRepository()
    repository.connect()
    try:
        outcome = repository.insert_mapping(mapping)

        assert outcome.inserted is False
        assert outcome.skipped_reason == "already_processed"
        assert outcome.employee_id is None
        # This run created nothing for this reference (outcome.employee_id
        # is None), so a cleanup correctly scoped to "employee_ids this run
        # created" has nothing to delete here -- the pre-existing audit
        # record must remain exactly as seeded, not duplicated or removed.
        with live_connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM processing_audit WHERE raw_event_ref = %s",
                (pre_existing_reference,),
            )
            audit_count = cursor.fetchone()
        assert audit_count == (1,)
    finally:
        with live_connection.cursor() as cleanup_cursor:
            cleanup_cursor.execute(
                "DELETE FROM processing_audit WHERE employee_id = %s",
                (pre_existing_employee_id,),
            )
            cleanup_cursor.execute(
                "DELETE FROM employees WHERE id = %s", (pre_existing_employee_id,)
            )
        live_connection.commit()
        repository.close()


def test_reprocessing_with_a_new_dependent_fragment_enriches_the_existing_employee(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    """HRP-57: the incomplete -> complete scenario HRP-51 defines at the
    transformation level. First pass has only the Personal fragment; second
    pass, same source_reference, adds a location that did not exist before.
    """
    from hr_pro_platform.storage.person_mapper import CandidateRow, PersonRecordMapping
    from hr_pro_platform.storage.person_repository import InsertOutcome, PersonRepository
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    schema_client = PostgresSchemaClient()
    schema_client.connect()
    try:
        schema_client.create_schema()
    finally:
        schema_client.close()

    source_reference = "integration-test-enrichment-source"
    passport = "INTEGRATION-TEST-P-ENRICH"

    def build_mapping(*, with_location: bool) -> PersonRecordMapping:
        return PersonRecordMapping(
            status="complete" if with_location else "incomplete",
            correlation_rules=(),
            provenance=(source_reference,),
            employees=(
                CandidateRow(
                    table="employees",
                    group_key=passport,
                    fields={
                        "first_name": "EnrichTest",
                        "last_name": "Fixture",
                        "passport": passport,
                    },
                    source_reference=source_reference,
                ),
            ),
            locations=(
                (
                    CandidateRow(
                        table="locations",
                        group_key="EnrichTest Fixture",
                        fields={"full_name": "EnrichTest Fixture", "city": "Springfield"},
                        source_reference=source_reference,
                    ),
                )
                if with_location
                else ()
            ),
            professional_profiles=(),
            bank_accounts=(),
            network_data=(),
        )

    repository = PersonRepository()
    repository.connect()
    first_outcome: InsertOutcome | None = None
    try:
        first_outcome = repository.insert_mapping(build_mapping(with_location=False))
        assert first_outcome.inserted is True
        assert first_outcome.employee_id is not None

        second_outcome = repository.insert_mapping(build_mapping(with_location=True))

        assert second_outcome.inserted is False
        assert second_outcome.employee_id == first_outcome.employee_id
        assert second_outcome.skipped_reason is None
        assert second_outcome.enriched_tables == ("locations",)

        # A third pass with the exact same location adds nothing further.
        third_outcome = repository.insert_mapping(build_mapping(with_location=True))
        assert third_outcome.inserted is False
        assert third_outcome.skipped_reason == "already_processed"
        assert third_outcome.enriched_tables == ()

        with live_connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM locations WHERE employee_id = %s",
                (first_outcome.employee_id,),
            )
            location_count = cursor.fetchone()
            cursor.execute(
                "SELECT count(*) FROM processing_audit WHERE raw_event_ref = %s",
                (source_reference,),
            )
            audit_count = cursor.fetchone()

        assert location_count == (1,)  # not duplicated by the third pass
        # HRP-58's unique index on raw_event_ref allows only one audit row
        # per source reference, so enrichment UPDATEs that row in place
        # (stage/status) rather than inserting a second one.
        assert audit_count == (1,)

        with live_connection.cursor() as cursor:
            cursor.execute(
                "SELECT stage, status FROM processing_audit WHERE raw_event_ref = %s",
                (source_reference,),
            )
            audit_row = cursor.fetchone()
        assert audit_row == ("update", "enriched")
    finally:
        if first_outcome is not None and first_outcome.employee_id is not None:
            with live_connection.cursor() as cleanup_cursor:
                cleanup_cursor.execute(
                    "DELETE FROM processing_audit WHERE employee_id = %s",
                    (first_outcome.employee_id,),
                )
                cleanup_cursor.execute(
                    "DELETE FROM employees WHERE id = %s", (first_outcome.employee_id,)
                )
            live_connection.commit()
        repository.close()


def test_replaying_a_dependent_row_with_null_fields_does_not_duplicate_it(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    """Real-database proof of NULL-safe equality: _dependent_row_exists
    compares every column with IS NOT DISTINCT FROM, not =. Plain SQL = is
    never true when either side is NULL, so a mock (where Python's
    None == None is simply True) cannot prove this -- only a live database
    enforcing real three-valued SQL logic can.
    """
    from hr_pro_platform.storage.person_mapper import CandidateRow, PersonRecordMapping
    from hr_pro_platform.storage.person_repository import PersonRepository
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    schema_client = PostgresSchemaClient()
    schema_client.connect()
    try:
        schema_client.create_schema()
    finally:
        schema_client.close()

    source_reference = "integration-test-null-safe-source"
    passport = "INTEGRATION-TEST-P-NULLSAFE"

    def build_mapping() -> PersonRecordMapping:
        return PersonRecordMapping(
            status="incomplete",
            correlation_rules=(),
            provenance=(source_reference,),
            employees=(
                CandidateRow(
                    table="employees",
                    group_key=passport,
                    fields={
                        "first_name": "NullSafe",
                        "last_name": "Fixture",
                        "passport": passport,
                    },
                    source_reference=source_reference,
                ),
            ),
            # full_name only: city, address, ip_v4 are absent -> persisted
            # as NULL. Replayed identically on every pass.
            locations=(
                CandidateRow(
                    table="locations",
                    group_key="NullSafe Fixture",
                    fields={"full_name": "NullSafe Fixture"},
                    source_reference=source_reference,
                ),
            ),
            professional_profiles=(),
            bank_accounts=(),
            network_data=(),
        )

    repository = PersonRepository()
    repository.connect()
    first_outcome = None
    try:
        first_outcome = repository.insert_mapping(build_mapping())
        assert first_outcome.inserted is True

        # The first pass already inserted employees + the NULL-heavy
        # location together, so both replays below must recognize the
        # existing NULL-valued row and add nothing -- that recognition,
        # despite three of its four columns being NULL, is exactly the
        # NULL-safe equality this test proves.
        second_outcome = repository.insert_mapping(build_mapping())
        assert second_outcome.skipped_reason == "already_processed"
        assert second_outcome.enriched_tables == ()

        third_outcome = repository.insert_mapping(build_mapping())
        assert third_outcome.skipped_reason == "already_processed"
        assert third_outcome.enriched_tables == ()

        with live_connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM locations WHERE employee_id = %s",
                (first_outcome.employee_id,),
            )
            location_count = cursor.fetchone()
        assert location_count == (1,)
    finally:
        if first_outcome is not None and first_outcome.employee_id is not None:
            with live_connection.cursor() as cleanup_cursor:
                cleanup_cursor.execute(
                    "DELETE FROM processing_audit WHERE employee_id = %s",
                    (first_outcome.employee_id,),
                )
                cleanup_cursor.execute(
                    "DELETE FROM employees WHERE id = %s", (first_outcome.employee_id,)
                )
            live_connection.commit()
        repository.close()


@pytest.mark.parametrize(
    "first_is_complete", [False, True], ids=["partial-then-complete", "complete-then-partial"]
)
def test_partial_and_complete_dependent_data_are_distinct_rows_in_both_orders(
    live_connection: psycopg.Connection[tuple[object, ...]],
    first_is_complete: bool,
) -> None:
    """Real-database proof of full-column (not subset) equality, in both
    possible arrival orders: a partial row (only full_name) and a complete
    row (full_name + city + address) for the same employee are genuinely
    different persisted rows once every column is compared -- regardless of
    which one arrives first. Also confirms replaying either exact input
    again does not grow the row count further, i.e. each of the two
    persisted rows is individually recognized on its own replay.
    """
    from hr_pro_platform.storage.person_mapper import CandidateRow, PersonRecordMapping
    from hr_pro_platform.storage.person_repository import PersonRepository
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    schema_client = PostgresSchemaClient()
    schema_client.connect()
    try:
        schema_client.create_schema()
    finally:
        schema_client.close()

    source_reference = f"integration-test-partial-complete-{first_is_complete}"
    passport = f"INTEGRATION-TEST-P-PARTIALCOMPLETE-{first_is_complete}"

    def build_mapping(*, complete: bool) -> PersonRecordMapping:
        fields: dict[str, object] = {"full_name": "PartialComplete Fixture"}
        if complete:
            fields["city"] = "Springfield"
            fields["address"] = "123 Main St"
        return PersonRecordMapping(
            status="incomplete",
            correlation_rules=(),
            provenance=(source_reference,),
            employees=(
                CandidateRow(
                    table="employees",
                    group_key=passport,
                    fields={
                        "first_name": "PartialComplete",
                        "last_name": "Fixture",
                        "passport": passport,
                    },
                    source_reference=source_reference,
                ),
            ),
            locations=(
                CandidateRow(
                    table="locations",
                    group_key="PartialComplete Fixture",
                    fields=fields,
                    source_reference=source_reference,
                ),
            ),
            professional_profiles=(),
            bank_accounts=(),
            network_data=(),
        )

    partial_mapping = build_mapping(complete=False)
    complete_mapping = build_mapping(complete=True)
    first_mapping = complete_mapping if first_is_complete else partial_mapping
    second_mapping = partial_mapping if first_is_complete else complete_mapping

    repository = PersonRepository()
    repository.connect()
    first_outcome = None
    try:
        first_outcome = repository.insert_mapping(first_mapping)
        assert first_outcome.inserted is True

        second_outcome = repository.insert_mapping(second_mapping)
        assert second_outcome.enriched_tables == ("locations",)

        # Replaying either exact input again must not grow the row count
        # further -- both the partial and the complete row must each be
        # individually recognized on their own replay.
        replay_first = repository.insert_mapping(first_mapping)
        replay_second = repository.insert_mapping(second_mapping)
        assert replay_first.enriched_tables == ()
        assert replay_second.enriched_tables == ()

        with live_connection.cursor() as cursor:
            cursor.execute(
                "SELECT city, address FROM locations "
                "WHERE employee_id = %s ORDER BY city NULLS FIRST",
                (first_outcome.employee_id,),
            )
            rows = cursor.fetchall()

        assert rows == [(None, None), ("Springfield", "123 Main St")]
    finally:
        if first_outcome is not None and first_outcome.employee_id is not None:
            with live_connection.cursor() as cleanup_cursor:
                cleanup_cursor.execute(
                    "DELETE FROM processing_audit WHERE employee_id = %s",
                    (first_outcome.employee_id,),
                )
                cleanup_cursor.execute(
                    "DELETE FROM employees WHERE id = %s", (first_outcome.employee_id,)
                )
            live_connection.commit()
        repository.close()


def test_concurrent_enrichment_of_the_same_reference_does_not_duplicate_a_dependent_row() -> None:
    """Real concurrency proof that _find_existing_employee_id's FOR UPDATE
    lock serialises two concurrent enrichment attempts for the same
    source_reference: without it, both could see "not yet present" and both
    insert the same new dependent row. Uses two separate connections and
    threads against the live database -- this cannot be demonstrated with a
    mock.

    Robustness of the test itself: every wait this test controls is bounded
    (both thread joins, the monitor's own polling window, and
    setup_connection's lock_timeout/statement_timeout). Termination of every
    thread this test started -- both workers and the monitor -- is verified
    explicitly rather than assumed from a timed join() returning, and errors
    from every thread (including the monitor) are captured and asserted on
    rather than silently swallowed. Contention is verified as specifically
    one worker blocked *by the other worker's own backend PID* via
    pg_blocking_pids(), not merely "some lock wait exists somewhere in the
    database", which could false-positive on unrelated concurrent activity.
    The one thing that cannot be bounded from this test alone is a worker's
    own database call hanging forever with no server-side timeout on that
    specific connection: Python cannot forcibly terminate a thread, and
    adding a lock_timeout to PersonRepository's own connection would be a
    production change, out of scope for this review round. If that ever
    happened, this test fails clearly on the is_alive() check below instead
    of hanging pytest indefinitely, and cleanup (via setup_connection, which
    does have a bounded lock_timeout) still runs and fails fast rather than
    hanging too.
    """
    import threading
    import time
    from unittest.mock import patch

    import psycopg

    from hr_pro_platform.storage.person_mapper import CandidateRow, PersonRecordMapping
    from hr_pro_platform.storage.person_repository import PersonRepository
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    try:
        from hr_pro_platform.storage.config import (
            POSTGRES_DB,
            POSTGRES_HOST,
            POSTGRES_PASSWORD,
            POSTGRES_PORT,
            POSTGRES_USER,
        )
    except OSError:
        pytest.skip("PostgreSQL environment variables are not configured (.env missing?).")

    try:
        # lock_timeout/statement_timeout bound every query this test issues
        # directly (monitor polling, cleanup): if anything goes wrong here,
        # a query fails fast with a clear Postgres error instead of hanging
        # the whole pytest run.
        setup_connection = psycopg.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            connect_timeout=2,
            options="-c lock_timeout=5000 -c statement_timeout=8000",
        )
    except psycopg.OperationalError:
        pytest.skip(
            "PostgreSQL is not reachable; "
            "start it with `docker compose -f infra/compose.dev.yml up -d postgres`."
        )
    # Autocommit is required for the monitor loop below: pg_stat_activity
    # reports live backend/wait-event state, but polling it repeatedly from
    # inside one long-held, never-committed transaction was empirically
    # observed to make every *other* backend's row disappear entirely from
    # the result -- confirmed by comparing otherwise-identical runs with and
    # without autocommit against a live database.
    setup_connection.autocommit = True

    schema_client = PostgresSchemaClient()
    schema_client.connect()
    try:
        schema_client.create_schema()
    finally:
        schema_client.close()

    source_reference = "integration-test-concurrent-source"
    passport = "INTEGRATION-TEST-P-CONCURRENT"

    def build_mapping() -> PersonRecordMapping:
        return PersonRecordMapping(
            status="incomplete",
            correlation_rules=(),
            provenance=(source_reference,),
            employees=(
                CandidateRow(
                    table="employees",
                    group_key=passport,
                    fields={
                        "first_name": "Concurrent",
                        "last_name": "Fixture",
                        "passport": passport,
                    },
                    source_reference=source_reference,
                ),
            ),
            locations=(
                CandidateRow(
                    table="locations",
                    group_key="Concurrent Fixture",
                    fields={"full_name": "Concurrent Fixture", "city": "Springfield"},
                    source_reference=source_reference,
                ),
            ),
            professional_profiles=(),
            bank_accounts=(),
            network_data=(),
        )

    seed_repository = PersonRepository()
    seed_repository.connect()
    seed_outcome = seed_repository.insert_mapping(
        PersonRecordMapping(
            status="incomplete",
            correlation_rules=(),
            provenance=(source_reference,),
            employees=(
                CandidateRow(
                    table="employees",
                    group_key=passport,
                    fields={
                        "first_name": "Concurrent",
                        "last_name": "Fixture",
                        "passport": passport,
                    },
                    source_reference=source_reference,
                ),
            ),
            locations=(),
            professional_profiles=(),
            bank_accounts=(),
            network_data=(),
        )
    )
    seed_repository.close()
    assert seed_outcome.inserted is True
    employee_id = seed_outcome.employee_id

    barrier = threading.Barrier(2)
    results: list[object] = [None, None]
    worker_pids: list[int | None] = [None, None]
    errors: list[BaseException] = []
    workers_done = threading.Event()

    def enrich(index: int) -> None:
        try:
            repository = PersonRepository()
            try:
                repository.connect()
                connection = repository._connection  # noqa: SLF001
                assert connection is not None
                worker_pids[index] = connection.info.backend_pid
                barrier.wait(timeout=5)
                results[index] = repository.insert_mapping(build_mapping())
            finally:
                repository.close()
        except BaseException as error:  # noqa: BLE001
            errors.append(error)

    # Bounded-wait proof of contention specifically between these two
    # workers -- not merely "some backend somewhere is waiting on some
    # lock", which could false-positive on unrelated concurrent activity in
    # a shared database. pg_blocking_pids() confirms one worker's own
    # backend PID is blocked *by the other worker's own backend PID*.
    contention_observed = threading.Event()
    monitor_errors: list[BaseException] = []

    def monitor() -> None:
        try:
            deadline = time.monotonic() + 5.0
            while not workers_done.is_set() and time.monotonic() < deadline:
                pids = [pid for pid in worker_pids if pid is not None]
                if len(pids) == 2:
                    with setup_connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT pid, pg_blocking_pids(pid) FROM pg_stat_activity "
                            "WHERE pid = ANY(%s) AND wait_event_type = 'Lock'",
                            (pids,),
                        )
                        rows = cursor.fetchall()
                    for blocked_pid, blocking_pids in rows:
                        other_pid = next(pid for pid in pids if pid != blocked_pid)
                        if other_pid in (blocking_pids or []):
                            contention_observed.set()
                            return
                time.sleep(0.01)
        except BaseException as error:  # noqa: BLE001
            monitor_errors.append(error)

    # Whichever worker acquires the FOR UPDATE lock first deliberately holds
    # it for a bounded, deterministic window before its transaction can
    # commit -- this is what makes the monitor's contention observation
    # reliable rather than dependent on both threads happening to race
    # within a few milliseconds of each other. This still exercises the
    # real, unmodified locking/enrichment logic; it only adds a delay after
    # the real lock has already been acquired.
    original_find_existing_employee_id = PersonRepository._find_existing_employee_id

    def held_find_existing_employee_id(cursor: object, source_reference: str) -> object:
        result = original_find_existing_employee_id(cursor, source_reference)
        time.sleep(1.0)
        return result

    threads = [threading.Thread(target=enrich, args=(i,)) for i in range(2)]
    monitor_thread = threading.Thread(target=monitor)
    with patch.object(
        PersonRepository,
        "_find_existing_employee_id",
        staticmethod(held_find_existing_employee_id),
    ):
        monitor_thread.start()
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=15)
        workers_done.set()
        monitor_thread.join(timeout=6)

    try:
        # Termination is verified explicitly for every thread this test
        # started -- a timed join() returning does not by itself prove a
        # thread finished; it may still be alive, and since Python cannot
        # forcibly terminate a thread, that is reported as a clear failure
        # here rather than silently proceeding as if nothing were wrong.
        assert all(not thread.is_alive() for thread in threads), (
            "a worker thread did not terminate within its bounded join timeout"
        )
        assert not monitor_thread.is_alive(), (
            "the monitor thread did not terminate within its bounded join timeout"
        )
        assert not errors, f"concurrent enrichment raised: {errors}"
        assert not monitor_errors, f"the contention monitor raised: {monitor_errors}"
        assert contention_observed.is_set(), (
            "monitor never observed one worker specifically blocked by the other "
            "worker's own backend PID -- the test did not actually exercise "
            "concurrent contention between these two workers on this run"
        )

        outcome_x, outcome_y = results
        assert outcome_x is not None and outcome_y is not None
        enriched = [outcome for outcome in (outcome_x, outcome_y) if outcome.enriched_tables]
        skipped = [
            outcome
            for outcome in (outcome_x, outcome_y)
            if outcome.skipped_reason == "already_processed"
        ]
        assert len(enriched) == 1, f"expected exactly one winner, got: {results}"
        assert enriched[0].enriched_tables == ("locations",)
        assert len(skipped) == 1, f"expected exactly one loser, got: {results}"
        assert skipped[0].enriched_tables == ()

        with setup_connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM locations WHERE employee_id = %s AND city = %s",
                (employee_id, "Springfield"),
            )
            location_count = cursor.fetchone()
        assert location_count == (1,)  # not duplicated by the concurrent second attempt
    finally:
        with setup_connection.cursor() as cleanup_cursor:
            cleanup_cursor.execute(
                "DELETE FROM processing_audit WHERE employee_id = %s", (employee_id,)
            )
            cleanup_cursor.execute("DELETE FROM employees WHERE id = %s", (employee_id,))
        setup_connection.close()


def test_enrichment_covers_all_four_dependent_tables_and_isolates_two_employees(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    """Real-database proof that enrichment works across all four dependent
    tables (not just locations, which every other test above happens to
    use) and that two distinct, sequentially-enriched employees never
    cross-contaminate each other's rows or each other's processing_audit
    marker. Both employees use IDENTICAL dependent-field values, so
    isolation is proven purely by employee_id scoping rather than
    incidentally by differing content. Uses two real, database-generated
    employee_id values -- a mock returning a single fixed id cannot
    demonstrate isolation between distinct ids.
    """
    from hr_pro_platform.storage.person_mapper import CandidateRow, PersonRecordMapping
    from hr_pro_platform.storage.person_repository import PersonRepository
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    schema_client = PostgresSchemaClient()
    schema_client.connect()
    try:
        schema_client.create_schema()
    finally:
        schema_client.close()

    shared_marker = "shared-marker"

    def bare_mapping(source_reference: str, passport: str, name: str) -> PersonRecordMapping:
        return PersonRecordMapping(
            status="incomplete",
            correlation_rules=(),
            provenance=(source_reference,),
            employees=(
                CandidateRow(
                    table="employees",
                    group_key=passport,
                    fields={"first_name": name, "last_name": "Fixture", "passport": passport},
                    source_reference=source_reference,
                ),
            ),
            locations=(),
            professional_profiles=(),
            bank_accounts=(),
            network_data=(),
        )

    def enriched_mapping(
        source_reference: str, passport: str, name: str, marker: str
    ) -> PersonRecordMapping:
        return PersonRecordMapping(
            status="complete",
            correlation_rules=(),
            provenance=(source_reference,),
            employees=(
                CandidateRow(
                    table="employees",
                    group_key=passport,
                    fields={"first_name": name, "last_name": "Fixture", "passport": passport},
                    source_reference=source_reference,
                ),
            ),
            locations=(
                CandidateRow(
                    table="locations",
                    group_key=f"{name} Fixture",
                    fields={"full_name": f"{name} Fixture", "city": marker},
                    source_reference=source_reference,
                ),
            ),
            professional_profiles=(
                CandidateRow(
                    table="professional_profiles",
                    group_key=f"{name} Fixture",
                    fields={"full_name": f"{name} Fixture", "job": marker},
                    source_reference=source_reference,
                ),
            ),
            bank_accounts=(
                CandidateRow(
                    table="bank_accounts",
                    group_key=passport,
                    fields={"iban": marker},
                    source_reference=source_reference,
                ),
            ),
            network_data=(
                CandidateRow(
                    table="network_data",
                    group_key=marker,
                    fields={"ip_v4": marker},
                    source_reference=source_reference,
                ),
            ),
        )

    ref_a, passport_a = "integration-test-isolation-source-A", "INTEGRATION-TEST-P-ISOLATION-A"
    ref_b, passport_b = "integration-test-isolation-source-B", "INTEGRATION-TEST-P-ISOLATION-B"

    all_tables = ("locations", "professional_profiles", "bank_accounts", "network_data")
    marker_column_by_table = {
        "locations": "city",
        "professional_profiles": "job",
        "bank_accounts": "iban",
        "network_data": "ip_v4",
    }

    def rows_for(employee_id: int, table: str) -> list[tuple[object, ...]]:
        marker_column = marker_column_by_table[table]
        with live_connection.cursor() as cursor:
            cursor.execute(
                f'SELECT employee_id, "{marker_column}" FROM {table} WHERE employee_id = %s',
                (employee_id,),
            )
            return list(cursor.fetchall())

    def audit_snapshot(employee_id: int) -> tuple[object, ...]:
        with live_connection.cursor() as cursor:
            cursor.execute(
                "SELECT stage, status, occurred_at FROM processing_audit "
                "WHERE employee_id = %s AND raw_event_ref IS NOT NULL",
                (employee_id,),
            )
            row = cursor.fetchone()
        assert row is not None
        return row

    repository = PersonRepository()
    repository.connect()
    outcome_a1 = outcome_b1 = None
    try:
        outcome_a1 = repository.insert_mapping(bare_mapping(ref_a, passport_a, "IsolationA"))
        outcome_b1 = repository.insert_mapping(bare_mapping(ref_b, passport_b, "IsolationB"))
        assert outcome_a1.inserted and outcome_b1.inserted
        assert outcome_a1.employee_id != outcome_b1.employee_id
        employee_id_a = outcome_a1.employee_id
        employee_id_b = outcome_b1.employee_id
        assert employee_id_a is not None and employee_id_b is not None

        # Snapshot B's audit marker before touching A at all, so the check
        # below proves enriching A leaves B's own marker completely alone.
        audit_before_a_enrichment = audit_snapshot(employee_id_b)

        outcome_a2 = repository.insert_mapping(
            enriched_mapping(ref_a, passport_a, "IsolationA", shared_marker)
        )
        assert set(outcome_a2.enriched_tables) == set(all_tables)

        assert audit_snapshot(employee_id_b) == audit_before_a_enrichment, (
            "enriching employee A modified employee B's processing_audit marker"
        )

        outcome_b2 = repository.insert_mapping(
            enriched_mapping(ref_b, passport_b, "IsolationB", shared_marker)
        )
        assert set(outcome_b2.enriched_tables) == set(all_tables)

        for table in all_tables:
            rows_a = rows_for(employee_id_a, table)
            rows_b = rows_for(employee_id_b, table)
            assert rows_a == [(employee_id_a, shared_marker)], (
                f"unexpected rows for employee A in {table}: {rows_a}"
            )
            assert rows_b == [(employee_id_b, shared_marker)], (
                f"unexpected rows for employee B in {table}: {rows_b}"
            )

        # Replay both enrichments with identical input: since both were
        # already fully enriched, no further rows should be inserted (a
        # dict-collapsed row fetch could hide a duplicate under the same
        # employee_id key, which is exactly why exact row lists are
        # asserted above and again here) and neither outcome should report
        # any newly-enriched table.
        replay_a = repository.insert_mapping(
            enriched_mapping(ref_a, passport_a, "IsolationA", shared_marker)
        )
        replay_b = repository.insert_mapping(
            enriched_mapping(ref_b, passport_b, "IsolationB", shared_marker)
        )
        assert replay_a.enriched_tables == ()
        assert replay_b.enriched_tables == ()
        for table in all_tables:
            assert rows_for(employee_id_a, table) == [(employee_id_a, shared_marker)], (
                f"replay duplicated a row for employee A in {table}"
            )
            assert rows_for(employee_id_b, table) == [(employee_id_b, shared_marker)], (
                f"replay duplicated a row for employee B in {table}"
            )
    finally:
        with live_connection.cursor() as cleanup_cursor:
            for outcome in (outcome_a1, outcome_b1):
                if outcome is not None and outcome.employee_id is not None:
                    cleanup_cursor.execute(
                        "DELETE FROM processing_audit WHERE employee_id = %s",
                        (outcome.employee_id,),
                    )
                    cleanup_cursor.execute(
                        "DELETE FROM employees WHERE id = %s", (outcome.employee_id,)
                    )
        live_connection.commit()
        repository.close()
