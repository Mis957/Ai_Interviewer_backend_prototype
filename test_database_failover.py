import unittest
from threading import Lock
import time
from types import SimpleNamespace

from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import app.core.database as database
import app.models
from app.models.question import Question


class DatabaseFailoverTests(unittest.TestCase):
    def setUp(self):
        self.original_state = (
            database._primary_engine,
            database._offline_engine,
            database._active_engine,
            database._using_offline_database,
            database._engine_lock,
            database._check_connection,
            database._last_sync_attempt,
            database._last_sync_succeeded_at,
            database._last_sync_error,
            database._last_primary_attempt,
            database._last_primary_error,
            database._sync_local_data_to_primary,
        )
        self.primary_engine = SimpleNamespace(
            dialect=SimpleNamespace(name="postgresql")
        )
        self.offline_engine = create_engine("sqlite:///:memory:")
        database._primary_engine = self.primary_engine
        database._offline_engine = self.offline_engine
        database._active_engine = self.primary_engine
        database._using_offline_database = False
        database._engine_lock = Lock()
        database._last_sync_attempt = 0.0
        database._last_sync_succeeded_at = None
        database._last_sync_error = None
        database._last_primary_attempt = 0.0
        database._last_primary_error = None

    def tearDown(self):
        (
            database._primary_engine,
            database._offline_engine,
            database._active_engine,
            database._using_offline_database,
            database._engine_lock,
            database._check_connection,
            database._last_sync_attempt,
            database._last_sync_succeeded_at,
            database._last_sync_error,
            database._last_primary_attempt,
            database._last_primary_error,
            database._sync_local_data_to_primary,
        ) = self.original_state
        self.offline_engine.dispose()

    def test_fails_over_and_creates_same_schema_locally(self):
        def check_connection(engine):
            if engine is self.primary_engine:
                raise SQLAlchemyError("simulated hosted database outage")

        database._check_connection = check_connection

        active_engine = database.get_active_engine()

        self.assertIs(active_engine, self.offline_engine)
        self.assertTrue(database.is_using_offline_database())
        inspector = inspect(active_engine)
        self.assertEqual(
            set(inspector.get_table_names()),
            set(database.Base.metadata.tables),
        )
        for table in database.Base.metadata.sorted_tables:
            self.assertEqual(
                {column["name"] for column in inspector.get_columns(table.name)},
                set(table.columns.keys()),
                table.name,
            )

    def test_retries_primary_and_switches_back_when_available(self):
        primary_checks = 0

        def check_connection(engine):
            nonlocal primary_checks
            if engine is self.primary_engine:
                primary_checks += 1
                if primary_checks == 1:
                    raise SQLAlchemyError("simulated hosted database outage")

        database._check_connection = check_connection
        database._sync_local_data_to_primary = lambda _local, _primary: None

        first_engine = database.get_active_engine()
        self.assertIs(first_engine, self.offline_engine)
        self.assertTrue(database.is_using_offline_database())
        self.assertEqual(primary_checks, 1)

        # The regular retry interval allows reconnect without hammering the pooler.
        database._last_primary_attempt = (
            time.monotonic() - database._sync_retry_interval_seconds - 1
        )
        second_engine = database.get_active_engine()

        self.assertIs(second_engine, self.primary_engine)
        self.assertEqual(primary_checks, 2)
        self.assertFalse(database.is_using_offline_database())

    def test_primary_connection_failure_is_throttled_and_reported(self):
        primary_checks = 0

        def check_connection(engine):
            nonlocal primary_checks
            if engine is self.primary_engine:
                primary_checks += 1
                raise SQLAlchemyError("simulated hosted database outage")

        database._check_connection = check_connection

        self.assertIs(database.get_active_engine(), self.offline_engine)
        self.assertIs(database.get_active_engine(), self.offline_engine)

        self.assertEqual(primary_checks, 1)
        status = database.get_offline_sync_status()
        self.assertEqual(status["status"], "waiting_for_connection")
        self.assertIn("simulated hosted database outage", status["error"])

    def test_hosted_database_becomes_active_even_if_sync_needs_retry(self):
        database._check_connection = lambda _engine: None

        def fail_sync(_local, _primary):
            raise SQLAlchemyError("simulated local sync failure")

        database._sync_local_data_to_primary = fail_sync

        active_engine = database.get_active_engine()

        self.assertIs(active_engine, self.primary_engine)
        self.assertFalse(database.is_using_offline_database())
        status = database.get_offline_sync_status()
        self.assertEqual(status["status"], "pending")
        self.assertIn("simulated local sync failure", status["error"])

    def test_sync_upserts_rows_and_keeps_local_records(self):
        primary_engine = create_engine("sqlite:///:memory:")
        database.Base.metadata.create_all(self.offline_engine)
        database.Base.metadata.create_all(primary_engine)
        try:
            with Session(self.offline_engine) as local_db:
                question = Question(
                    technology="Python",
                    topic="Basics",
                    difficulty="Easy",
                    question="What is a variable?",
                    expected_answer="A named value.",
                    keywords=["variable"],
                )
                local_db.add(question)
                local_db.commit()
                question_id = question.id

            database._sync_local_data_to_primary(
                self.offline_engine,
                primary_engine,
            )
            database._sync_local_data_to_primary(
                self.offline_engine,
                primary_engine,
            )

            with Session(primary_engine) as primary_db:
                synced = primary_db.get(Question, question_id)
                self.assertIsNotNone(synced)
                self.assertEqual(synced.question, "What is a variable?")
                self.assertEqual(primary_db.query(Question).count(), 1)

            with Session(self.offline_engine) as local_db:
                local_question = local_db.get(Question, question_id)
                self.assertIsNotNone(local_question)
                local_question.question = "What is a Python variable?"
                local_db.commit()

            database._sync_local_data_to_primary(
                self.offline_engine,
                primary_engine,
            )

            with Session(primary_engine) as primary_db:
                synced = primary_db.get(Question, question_id)
                self.assertEqual(synced.question, "What is a Python variable?")
                self.assertEqual(primary_db.query(Question).count(), 1)
        finally:
            primary_engine.dispose()


if __name__ == "__main__":
    unittest.main()
