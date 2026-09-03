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


def test_partial_then_complete_dependent_data_is_not_treated_as_the_same_row(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    """Real-database proof of full-column (not subset) equality: a partial
    row (only full_name) and a later complete row (full_name + city +
    address) for the same employee are genuinely different persisted rows
    once every column is compared, not just the columns the incoming
    candidate happens to mention.
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

    source_reference = "integration-test-partial-complete-source"
    passport = "INTEGRATION-TEST-P-PARTIALCOMPLETE"

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

    repository = PersonRepository()
    repository.connect()
    first_outcome = None
    try:
        first_outcome = repository.insert_mapping(build_mapping(complete=False))
        assert first_outcome.inserted is True

        second_outcome = repository.insert_mapping(build_mapping(complete=True))
        assert second_outcome.enriched_tables == ("locations",)

        with live_connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM locations WHERE employee_id = %s",
                (first_outcome.employee_id,),
            )
            location_count = cursor.fetchone()
        assert location_count == (2,)  # partial and complete are distinct rows
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
    """
    import threading

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
        setup_connection = psycopg.connect(
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
    errors: list[BaseException] = []

    def enrich(index: int) -> None:
        repository = PersonRepository()
        repository.connect()
        try:
            barrier.wait(timeout=5)
            results[index] = repository.insert_mapping(build_mapping())
        except BaseException as error:  # noqa: BLE001
            errors.append(error)
        finally:
            repository.close()

    threads = [threading.Thread(target=enrich, args=(i,)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=15)

    try:
        assert not errors, f"concurrent enrichment raised: {errors}"
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
        setup_connection.commit()
        setup_connection.close()
